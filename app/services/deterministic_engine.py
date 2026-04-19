import re
from typing import Any, Dict, List, Optional, Tuple

from app.agents.executor import Executor
from app.services.confidence import ConfidenceService
from app.services.data_loader import DataLoader
from app.services.llm_engine import LLMSupportEngine
from app.schemas.order import Order
from config import settings


ORDER_ID_RE = re.compile(r"\bORD-\d+\b", re.IGNORECASE)


class DeterministicSupportEngine:
    """Fallback support engine that keeps the hackathon flow working without external LLM packages."""

    def __init__(self, audit_logger):
        self.audit = audit_logger
        self.executor = Executor()
        self.llm_engine = LLMSupportEngine(audit_logger)

    async def run(self, ticket: Dict[str, Any], customer: Dict[str, Any]) -> Dict[str, Any]:
        ticket_id = ticket["ticket_id"]
        order_id = self._extract_order_id(ticket)
        intent = self._detect_intent(ticket)

        # Log planner decision with reasoning
        self.audit.log_event(ticket_id, "planner_decision", {
            "decision": f"Detected intent: {intent}",
            "confidence": "high",
            "reasoning": f"Intent detection based on keywords in ticket text: {intent.replace('_', ' ')}"
        })

        plan = self._build_plan(ticket, customer, order_id, intent)
        self.audit.log_event(ticket_id, "plan_created", {"intent": intent, "plan": plan})

        execution_results = await self.executor.execute_plan(plan)
        self.audit.log_event(ticket_id, "tools_executed", {"results": execution_results})

        # Log intermediate reasoning before evaluation
        self.audit.log_event(ticket_id, "intermediate_reasoning", {
            "step": "pre_evaluation",
            "reasoning": f"Evaluating {intent} request for order {order_id or 'unknown'} with customer verification and policy checks"
        })

        resolution = self._evaluate(ticket, customer, order_id, intent)

        # Log intermediate reasoning after evaluation
        self.audit.log_event(ticket_id, "intermediate_reasoning", {
            "step": "post_evaluation",
            "reasoning": f"Initial resolution determined: {resolution.get('status')} with reasoning: {resolution.get('reasoning')}"
        })

        resolution = await self.llm_engine.evaluate_resolution(ticket, customer, execution_results, resolution)

        # Log LLM enhancement
        self.audit.log_event(ticket_id, "intermediate_reasoning", {
            "step": "llm_enhancement",
            "reasoning": "LLM engine reviewed and potentially enhanced the resolution response"
        })

        resolution = self._enforce_hard_rules(ticket, order_id, intent, resolution)
        resolution["tool_results"] = execution_results
        self.audit.log_event(ticket_id, "resolution_completed", resolution)
        return resolution

    def _extract_order_id(self, ticket: Dict[str, Any]) -> Optional[str]:
        if ticket.get("order_id"):
            return ticket["order_id"]
        search_space = " ".join(filter(None, [ticket.get("subject", ""), ticket.get("body", "")]))
        match = ORDER_ID_RE.search(search_space)
        return match.group(0).upper() if match else None

    def _detect_intent(self, ticket: Dict[str, Any]) -> str:
        text = f"{ticket.get('subject', '')} {ticket.get('body', '')}".lower()
        if "cancel" in text:
            return "cancellation"
        if "where is my order" in text or "tracking" in text or "haven't received" in text:
            return "shipping_status"
        if "return policy" in text or "what is your return policy" in text or "what's the process" in text:
            return "policy_question"
        if "wrong size" in text or "wrong colour" in text or "wrong color" in text or "wrong item" in text:
            return "exchange"
        if any(keyword in text for keyword in ["damaged", "cracked", "broken", "defect", "stopped working", "not working"]):
            return "damage_or_defect"
        if "refund" in text or "return" in text:
            return "refund"
        return "clarification"

    def _build_plan(
        self,
        ticket: Dict[str, Any],
        customer: Dict[str, Any],
        order_id: Optional[str],
        intent: str,
    ) -> List[Dict[str, Any]]:
        plan: List[Dict[str, Any]] = []
        customer_id = customer.get("customer_id") or ticket.get("customer_email")

        if customer_id:
            plan.append({"tool_name": "get_customer_profile", "parameters": {"customer_id": customer_id}})

        if order_id:
            plan.append({"tool_name": "get_order_details", "parameters": {"order_id": order_id}})
        elif customer_id:
            plan.append({"tool_name": "get_customer_orders", "parameters": {"customer_id": customer_id}})

        if intent == "cancellation" and order_id:
            plan.append({"tool_name": "check_cancellation_eligibility", "parameters": {"order_id": order_id}})
        elif intent == "shipping_status" and order_id:
            plan.append({"tool_name": "get_shipping_status", "parameters": {"order_id": order_id}})
        elif intent in {"refund", "damage_or_defect", "exchange"} and order_id:
            plan.append(
                {
                    "tool_name": "check_refund_eligibility",
                    "parameters": {"order_id": order_id, "customer_id": customer_id},
                }
            )
        else:
            plan.append({"tool_name": "get_policy_info", "parameters": {"keywords": intent.replace("_", " ")}})

        return plan

    def _log_policy_check(self, ticket_id: str, check: str, result: str, details: Optional[str] = None) -> None:
        entry = {
            "check": check,
            "result": result,
        }
        if details:
            entry["details"] = details
        self.audit.log_event(ticket_id, "policy_check", entry)

    def _evaluate(self, ticket: Dict[str, Any], customer: Dict[str, Any], order_id: Optional[str], intent: str) -> Dict[str, Any]:
        ticket_id = ticket["ticket_id"]
        first_name = customer.get("first_name") or "there"
        order = self._load_order(order_id)
        text = f"{ticket.get('subject', '')} {ticket.get('body', '')}".lower()

        if not customer:
            self.audit.log_event(ticket_id, "intermediate_reasoning", {
                "step": "customer_verification",
                "reasoning": "Customer identity verification failed - no customer record found"
            })
            self._log_policy_check(ticket_id, "customer_verification", "failed", "Customer identity could not be verified")
            return self._resolution(
                ticket_id,
                "escalate",
                0.35,
                "Customer identity could not be verified in the system.",
                "Support Operations",
                "Hi, I’m unable to verify your account yet. Please reply with your order ID and registered email so we can help.",
            )

        if not order_id:
            self.audit.log_event(ticket_id, "intermediate_reasoning", {
                "step": "order_extraction",
                "reasoning": "No order ID found in ticket - requesting clarification from customer"
            })
            self._log_policy_check(ticket_id, "order_id_presence", "missing", "No order ID found in ticket text")
            return self._resolution(
                ticket_id,
                "resolved",
                0.72,
                "The ticket is missing an order ID, so the next best action is to request clarification.",
                None,
                f"Hi {first_name}, I’m happy to help. Please share your order ID so I can check the details and take the right next step.",
            )

        if order is None:
            self.audit.log_event(ticket_id, "intermediate_reasoning", {
                "step": "order_lookup",
                "reasoning": f"Order {order_id} not found in system - requesting corrected order ID"
            })
            self._log_policy_check(ticket_id, "order_lookup", "failed", f"Order {order_id} not found")
            return self._resolution(
                ticket_id,
                "resolved",
                0.7,
                "The provided order ID was not found, so a clarification response is safest.",
                None,
                f"Hi {first_name}, I couldn’t find order {order_id} in our system. Please double-check the order number and send it over so I can continue.",
            )

        if "premium policy" in text or "instant refunds without questions" in text:
            self.audit.log_event(ticket_id, "intermediate_reasoning", {
                "step": "fraud_detection",
                "reasoning": "Detected potential social engineering phrases - escalating for human review"
            })
            self._log_policy_check(ticket_id, "fraud_detection", "triggered", "Potential social engineering phrase detected")
            return self._resolution(
                ticket_id,
                "escalate",
                0.55,
                "Potential social-engineering or fraudulent policy claims were detected and should be reviewed by a human.",
                "Fraud Team",
                f"Hi {first_name}, I’ve routed this case to a specialist for review so we can handle it appropriately.",
            )

        if intent == "cancellation":
            self.audit.log_event(ticket_id, "intermediate_reasoning", {
                "step": "cancellation_evaluation",
                "reasoning": f"Evaluating cancellation request for order {order_id} with status {order.status}"
            })
            self._log_policy_check(ticket_id, "cancellation_policy", "evaluated", f"Order status is {order.status}")
            if order.status == "processing":
                return self._resolution(
                    ticket_id,
                    "resolved",
                    0.94,
                    "The order is still processing and is eligible for cancellation.",
                    None,
                    f"Hi {first_name}, your order {order_id} is still processing, so it can be cancelled. I’ve marked it for cancellation and a full refund.",
                )
            return self._resolution(
                ticket_id,
                "resolved",
                0.9,
                f"Order {order_id} is already {order.status}, so it can no longer be cancelled.",
                None,
                f"Hi {first_name}, order {order_id} is already {order.status}, so it can’t be cancelled at this stage.",
            )

        if intent == "shipping_status":
            self.audit.log_event(ticket_id, "intermediate_reasoning", {
                "step": "shipping_status_evaluation",
                "reasoning": f"Retrieving shipping status for order {order_id} with status {order.status}"
            })
            self._log_policy_check(ticket_id, "shipping_status", "evaluated", f"Order status is {order.status}")
            return self._resolution(
                ticket_id,
                "resolved",
                0.95,
                "Shipping status was retrieved successfully.",
                None,
                self._shipping_message(order, order_id, first_name),
            )

        if intent == "policy_question":
            self.audit.log_event(ticket_id, "intermediate_reasoning", {
                "step": "policy_question_evaluation",
                "reasoning": "Providing policy information to customer"
            })
            self._log_policy_check(ticket_id, "policy_information", "evaluated", "Customer requested policy details")
            return self._resolution(
                ticket_id,
                "resolved",
                0.88,
                "This is an informational policy request.",
                None,
                f"Hi {first_name}, standard returns are 30 days, electronics accessories are 60 days, and high-value electronics are 15 days. If you want, I can also walk you through the steps for order {order_id} specifically.",
            )

        if intent == "damage_or_defect":
            self.audit.log_event(ticket_id, "intermediate_reasoning", {
                "step": "damage_defect_evaluation",
                "reasoning": f"Evaluating damage/defect claim for order {order_id} - checking eligibility based on order age and amount"
            })
            self._log_policy_check(ticket_id, "damage_assessment", "evaluated", f"Order total {order.total_amount}, days since order {order.days_since_order}")
            if "replacement" in text or "warranty" in text or order.days_since_order > settings.STANDARD_RETURN_DAYS:
                return self._resolution(
                    ticket_id,
                    "escalate",
                    0.84,
                    "Replacement, warranty-style, or outside-window defect claims require specialist review under policy.",
                    "Warranty Team",
                    f"Hi {first_name}, I’ve escalated this to our specialist team so they can handle the replacement or warranty review for order {order_id}.",
                )

            if order.total_amount > settings.MAX_REFUND_AUTO_APPROVE:
                return self._resolution(
                    ticket_id,
                    "escalate",
                    0.86,
                    "The item appears damaged or defective, but the refund amount exceeds the auto-approval limit.",
                    "Supervisor",
                    f"Hi {first_name}, I’ve escalated order {order_id} for review because the refund requires supervisor approval.",
                )

            return self._resolution(
                ticket_id,
                "resolved",
                0.9,
                "Damaged-on-arrival issue can be handled under standard refund policy.",
                None,
                f"Hi {first_name}, thanks for flagging this. Based on the details for order {order_id}, your damaged-item refund is eligible and our team can process it with the usual 5-7 business day timeline.",
            )

        if intent == "exchange":
            self._log_policy_check(ticket_id, "exchange_policy", "evaluated", "Exchange allowed under policy")
            return self._resolution(
                ticket_id,
                "resolved",
                0.89,
                "Wrong-item exchanges are allowed by policy.",
                None,
                f"Hi {first_name}, I’ve confirmed order {order_id} falls under our exchange policy for wrong-item issues. We can move forward with an exchange, or a refund if stock is unavailable.",
            )

        if intent == "refund":
            within_window, window_reason = self._refund_window_decision(order)
            self._log_policy_check(ticket_id, "refund_eligibility", "evaluated", window_reason)
            if not within_window:
                if customer.get("tier", "").upper() == "VIP":
                    return self._resolution(
                        ticket_id,
                        "resolved",
                        0.78,
                        f"{window_reason} VIP leniency applies here.",
                        None,
                        f"Hi {first_name}, this order is outside the standard return window, but I can note the VIP exception path for review and help move it forward.",
                    )
                return self._resolution(
                    ticket_id,
                    "resolved",
                    0.85,
                    window_reason,
                    None,
                    f"Hi {first_name}, order {order_id} is outside the allowed return window, so I’m unable to approve a refund under policy.",
                )

            if order.total_amount > settings.MAX_REFUND_AUTO_APPROVE:
                self._log_policy_check(ticket_id, "refund_amount_limit", "triggered", f"Order amount {order.total_amount} exceeds auto-approve limit")
                return self._resolution(
                    ticket_id,
                    "escalate",
                    0.9,
                    "The order is otherwise eligible, but the refund amount exceeds the auto-approval limit.",
                    "Supervisor",
                    f"Hi {first_name}, order {order_id} is eligible for review, but I’ve escalated it because refunds above ${settings.MAX_REFUND_AUTO_APPROVE:.0f} require supervisor approval.",
                )

            return self._resolution(
                ticket_id,
                "resolved",
                0.93,
                "Refund is within policy and under the auto-approval threshold.",
                None,
                f"Hi {first_name}, order {order_id} is eligible for a refund under our policy. Once processed, the funds usually appear within 5-7 business days.",
            )

        return self._resolution(
            ticket_id,
            "resolved",
            0.68,
            "The issue is too ambiguous for an automated action, so the safest response is clarification.",
            None,
            f"Hi {first_name}, I want to make sure I help with the right issue. Please share your order ID and a bit more detail about what went wrong.",
        )

    def _load_order(self, order_id: Optional[str]) -> Optional[Order]:
        if not order_id:
            return None
        return DataLoader.find_by_id(str(settings.ORDER_DATA), Order, "order_id", order_id)

    def _refund_window_decision(self, order: Order) -> Tuple[bool, str]:
        categories = [item.category.lower() for item in order.items]
        max_days = settings.STANDARD_RETURN_DAYS
        if "high-value electronics" in categories:
            max_days = settings.HIGH_VALUE_ELECTRONICS_RETURN_DAYS
        elif "electronics accessories" in categories:
            max_days = settings.ELECTRONICS_ACCESSORIES_RETURN_DAYS

        if order.days_since_order > max_days:
            return False, f"Order is outside the {max_days}-day return window."
        return True, f"Order is within the {max_days}-day return window."

    def _shipping_message(self, order: Order, order_id: str, first_name: str) -> str:
        if order.status == "processing":
            return f"Hi {first_name}, order {order_id} is still being prepared for shipment. I’ll recommend checking back once the tracking number is generated."
        if order.status == "shipped":
            tracking = order.tracking_number or "tracking pending"
            return f"Hi {first_name}, order {order_id} is in transit. Your tracking reference is {tracking}."
        if order.status == "delivered":
            return f"Hi {first_name}, our records show order {order_id} has already been delivered to {order.shipping_address}."
        return f"Hi {first_name}, order {order_id} is currently marked as {order.status}."

    def _resolution(
        self,
        ticket_id: str,
        status: str,
        confidence: float,
        reasoning: str,
        escalation_team: Optional[str],
        final_message: str,
    ) -> Dict[str, Any]:
        if ConfidenceService.should_escalate(confidence):
            status = "escalate"
            escalation_team = escalation_team or "Support Operations"
            reasoning = f"{reasoning} Confidence fell below threshold, so the case was escalated."

        return {
            "ticket_id": ticket_id,
            "status": status,
            "reasoning": reasoning,
            "confidence_score": confidence,
            "final_message": final_message,
            "escalation_team": escalation_team,
        }

    def _enforce_hard_rules(
        self,
        ticket: Dict[str, Any],
        order_id: Optional[str],
        intent: str,
        resolution: Dict[str, Any],
    ) -> Dict[str, Any]:
        order = self._load_order(order_id)
        text = f"{ticket.get('subject', '')} {ticket.get('body', '')}".lower()

        if resolution.get("confidence_score", 0.0) < settings.CONFIDENCE_THRESHOLD_ESCALATE:
            resolution["status"] = "escalate"
            resolution["escalation_team"] = resolution.get("escalation_team") or "Support Operations"
            return resolution

        if order and order.total_amount > settings.MAX_REFUND_AUTO_APPROVE and intent in {"refund", "damage_or_defect"}:
            resolution["status"] = "escalate"
            resolution["escalation_team"] = "Supervisor"
            return resolution

        if intent == "damage_or_defect" and (
            "replacement" in text or "warranty" in text or (order and order.days_since_order > settings.STANDARD_RETURN_DAYS)
        ):
            resolution["status"] = "escalate"
            resolution["escalation_team"] = "Warranty Team"
            return resolution

        return resolution
