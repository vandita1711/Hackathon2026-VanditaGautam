from typing import Dict, Any, List
from pydantic import BaseModel, Field

class TicketState(BaseModel):
    ticket_id: str
    steps: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    plan: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []
    resolution: Dict[str, Any] = {}

class Memory:
    """Manages short-term state for tickets during processing."""
    def __init__(self):
        self._storage: Dict[str, TicketState] = {}

    def get_context(self, ticket_id: str) -> TicketState:
        if ticket_id not in self._storage:
            self._storage[ticket_id] = TicketState(ticket_id=ticket_id)
        return self._storage[ticket_id]

    def update_step(self, ticket_id: str, key: str, value: Any):
        state = self.get_context(ticket_id)
        setattr(state, key, value)

    def clear(self, ticket_id: str):
        if ticket_id in self._storage:
            del self._storage[ticket_id]
