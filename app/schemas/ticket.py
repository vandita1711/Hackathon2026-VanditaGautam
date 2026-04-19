from pydantic import AliasChoices, BaseModel, Field
from typing import Optional, List
from enum import Enum

class TicketStatus(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Ticket(BaseModel):
    ticket_id: str
    customer_id: str = Field(
        ...,
        validation_alias=AliasChoices("customer_id", "customer_email"),
    )
    subject: str
    body: str = Field(
        ...,
        validation_alias=AliasChoices("body", "description"),
    )
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    created_at: str
    order_id: Optional[str] = None
    category: Optional[str] = None
    history: List[str] = []
    
    # Fallback to description for internal logic if needed
    @property
    def description(self) -> str:
        return self.body

    @property
    def customer_email(self) -> str:
        return self.customer_id

    class Config:
        use_enum_values = True
        populate_by_name = True
