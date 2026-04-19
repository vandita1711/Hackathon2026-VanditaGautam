from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

class Customer(BaseModel):
    customer_id: str = Field(..., alias="customer_id")
    first_name: str
    last_name: str
    email: str
    tier: str
    join_date: str
    notes: Optional[str] = ""
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="allow")

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_customer_shape(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        full_name = str(normalized.get("name") or "").strip()

        if not normalized.get("first_name"):
            if full_name:
                parts = full_name.split()
                normalized["first_name"] = parts[0]
                normalized["last_name"] = " ".join(parts[1:]) if len(parts) > 1 else ""
            else:
                normalized["first_name"] = ""

        if not normalized.get("last_name"):
            normalized["last_name"] = ""

        if not normalized.get("join_date"):
            normalized["join_date"] = normalized.get("member_since") or ""

        tier = normalized.get("tier")
        if isinstance(tier, str):
            normalized["tier"] = tier.upper()

        return normalized

    @property
    def id(self) -> str:
        return self.customer_id
