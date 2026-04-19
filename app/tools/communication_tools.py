from app.core.logger import logger
from .tool_registry import registry

@registry.register(description="Draft a response message to the customer.")
def send_reply(ticket_id: str, message: str) -> str:
    logger.info(f"DRAFTING REPLY for {ticket_id}: {message}")
    return f"Success: Reply drafted for ticket {ticket_id}."

@registry.register(description="Escalate the ticket to a human agent.")
def escalate_ticket(ticket_id: str, reason: str) -> str:
    logger.warning(f"ESCALATION for {ticket_id}: {reason}")
    return f"Success: Ticket {ticket_id} escalated for reason: {reason}."
