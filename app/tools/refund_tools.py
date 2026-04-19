from typing import Dict, Any, Optional
from app.services.data_loader import DataLoader
from app.schemas.order import Order
from app.schemas.customer import Customer
from config import settings
from .tool_registry import registry

@registry.register(description="Determine if a customer is eligible for a refund.")
def check_refund_eligibility(order_id: str, customer_id: Optional[str] = None) -> str:
    order = DataLoader.find_by_id(str(settings.ORDER_DATA), Order, "order_id", order_id)
    if not order: 
        return f"Order {order_id} not found."
    
    cid = customer_id or order.customer_id
    customer = DataLoader.find_by_id(str(settings.CUSTOMER_DATA), Customer, "customer_id", cid)
    if not customer: 
        return f"Customer {cid} not found."

    days_since = order.days_since_order
    max_days = settings.STANDARD_RETURN_DAYS
    categories = [item.category.lower() for item in order.items]
    
    if "high-value electronics" in categories:
        max_days = settings.HIGH_VALUE_ELECTRONICS_RETURN_DAYS
    elif "electronics accessories" in categories:
        max_days = settings.ELECTRONICS_ACCESSORIES_RETURN_DAYS
        
    if days_since > max_days:
        if customer.tier == "VIP":
            return f"Outside window ({days_since} days > {max_days} days). Note: Customer is VIP, borderline leniency possible."
        return f"Ineligible: Return window exceeded ({days_since} days > {max_days} days)."

    return f"Eligible: Order is within the {max_days}-day return window."

@registry.register(description="Process a refund for an order.")
def execute_refund(order_id: str, amount: float, reason: str) -> str:
    if amount > settings.MAX_REFUND_AUTO_APPROVE:
        return f"Escalation Required: Refund amount ${amount} exceeds auto-approval limit of ${settings.MAX_REFUND_AUTO_APPROVE}."
    return f"Success: Refund of ${amount:.2f} processed for order {order_id}. Reason: {reason}."
