import json
import asyncio
from app.core.memory import Memory
from app.services.audit_logger import AuditLogger
from app.services.deterministic_engine import DeterministicSupportEngine
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from app.agents.autogen_agents import AutoGenAgentFactory
from app.core.logger import logger
from config import settings
from config.autogen_config import get_llm_config

try:
    from openai import AuthenticationError as OpenAIAuthError
except ImportError:
    OpenAIAuthError = None  # type: ignore


class Orchestrator:
    """Orchestrates the lifecycle of a ticket using AutoGen 0.7+ Multi-Agent conversation."""

    def __init__(self):
        self.memory = Memory()
        self.audit = AuditLogger()
        self.fallback_engine = DeterministicSupportEngine(self.audit)

    def _parse_autogen_json(self, ticket_id: str, text: str) -> dict:
        from json import JSONDecoder
        import re

        stripped = text.strip()
        if not stripped:
            self.audit.log_event(ticket_id, "autogen_parse_error", {"error": "Empty AutoGen response."})
            raise ValueError("Empty AutoGen response")

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            start = stripped.find("{")
            if start == -1:
                self.audit.log_event(ticket_id, "autogen_parse_error", {"error": "No JSON object found in response."})
                raise

            decoder = JSONDecoder()
            try:
                resolution, _ = decoder.raw_decode(stripped, idx=start)
                return resolution
            except json.JSONDecodeError:

                # ✅ FIX: extract LAST valid JSON only (ignores tool plan)
                matches = re.findall(r"\{.*?\}", stripped, re.DOTALL)

                if matches:
                    for m in reversed(matches):
                        try:
                            return json.loads(m)
                        except:
                            continue

                self.audit.log_event(ticket_id, "autogen_parse_error", {"error": "No valid JSON object found after fallback parse."})
                raise

    @staticmethod
    def _format_autogen_error(exc: BaseException) -> str:
        if OpenAIAuthError is not None and isinstance(exc, OpenAIAuthError):
            return (
                "LLM authentication failed (401): check that your key matches the provider — "
                "GROQ_API_KEY with Groq (api.groq.com) or OPENAI_API_KEY with api.openai.com. "
                f"Original: {exc}"[:400]
            )
        msg = str(exc)
        if len(msg) > 800:
            return msg[:800] + "…"
        return msg

    async def process_ticket(self, ticket: dict, customer: dict) -> dict:
        ticket_id = ticket["ticket_id"]
        logger.info(f"Starting orchestration for ticket: {ticket_id}")
        self.audit.log_event(ticket_id, "ticket_received", {"ticket": ticket, "customer": customer})

        if not settings.ENABLE_LLM:
            self.audit.log_event(ticket_id, "autogen_skipped", {"reason": "ENABLE_LLM is false"})
            return await self.fallback_engine.run(ticket, customer)

        if get_llm_config() is None:
            self.audit.log_event(
                ticket_id,
                "autogen_skipped",
                {"reason": "No GROQ_API_KEY or OPENAI_API_KEY configured"},
            )
            return await self.fallback_engine.run(ticket, customer)

        try:
            self.audit.log_event(ticket_id, "autogen_started", {"ticket_id": ticket_id})

            planner, executor, critic = AutoGenAgentFactory.create_agents(ticket_id)

            termination = TextMentionTermination("TERMINATE")

            team = RoundRobinGroupChat(
                [planner, executor, critic],
                termination_condition=termination
            )

            initial_message = f"Process this support ticket: {json.dumps(ticket)}\nCustomer: {json.dumps(customer)}"

            loop = asyncio.get_event_loop()

            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: asyncio.new_event_loop().run_until_complete(
                            team.run(task=initial_message)
                        )
                    ),
                    timeout=20
                )
            except asyncio.TimeoutError:
                raise Exception("AutoGen timeout after 20 seconds")

            last_msg = result.messages[-1] if getattr(result, "messages", None) else None

            if last_msg is None:
                final_message = "No response"
            else:
                final_message = getattr(last_msg, "content", None) or (
                    last_msg.to_text() if hasattr(last_msg, "to_text") else str(last_msg)
                )

            self.audit.log_event(ticket_id, "autogen_completed", {"final_message": final_message})

            self.audit.log_event(
                ticket_id,
                "autogen_response",
                {
                    "raw_messages": [
                        {
                            "source": getattr(message, "source", None),
                            "content": getattr(message, "content", None)
                            or (message.to_text() if hasattr(message, "to_text") else str(message)),
                        }
                        for message in getattr(result, "messages", [])
                    ],
                    "final_message": final_message,
                },
            )

            resolution = self._parse_autogen_json(ticket_id, final_message)

            if not isinstance(resolution, dict):
                raise ValueError("AutoGen response did not return a JSON object")

            resolution["ticket_id"] = ticket_id

            self.audit.log_event(ticket_id, "resolution_completed", resolution)

            return resolution

        except Exception as e:
            err_text = self._format_autogen_error(e)

            self.audit.log_event(ticket_id, "autogen_failed", {"error": err_text})

            logger.warning(f"AutoGen failed, falling back to deterministic: {err_text}")

            fallback_result = await self.fallback_engine.run(ticket, customer)

            self.audit.log_event(
                ticket_id,
                "fallback_used",
                {
                    "reason": err_text,
                    "fallback_status": fallback_result.get("status"),
                    "confidence_score": fallback_result.get("confidence_score"),
                    "reasoning": fallback_result.get("reasoning"),
                },
            )

            return fallback_result

        finally:
            self.memory.clear(ticket_id)