from typing import Any, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

class OrderItem(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    quantity: int

class Order(BaseModel):
    order_id: str
    customer_id: str
    order_date: str
    status: str = Field(..., description="processing, shipped, delivered, cancelled")
    items: List[OrderItem]
    total_amount: float
    shipping_address: Optional[str] = "Address not provided"
    tracking_number: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_flat_order_shape(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        if not normalized.get("items") and normalized.get("product_id"):
            quantity = int(normalized.get("quantity") or 1)
            amount = float(normalized.get("amount") or 0)
            category = cls._infer_category(normalized)
            normalized["items"] = [
                {
                    "product_id": normalized["product_id"],
                    "name": normalized.get("product_name") or normalized["product_id"],
                    "category": category,
                    "price": amount / quantity if quantity else amount,
                    "quantity": quantity,
                }
            ]

        if normalized.get("total_amount") is None:
            normalized["total_amount"] = float(normalized.get("amount") or 0)

        return normalized

    @staticmethod
    def _infer_category(order_data: dict) -> str:
        notes = str(order_data.get("notes") or "").lower()
        if "15-day return window" in notes or "high-value item" in notes:
            return "high-value electronics"
        if "accessor" in notes:
            return "electronics accessories"
        return "general merchandise"

    @property
    def days_since_order(self) -> int:
        try:
            order_dt = datetime.fromisoformat(self.order_date.replace("Z", "+00:00"))
            return max((datetime.now(order_dt.tzinfo) - order_dt).days, 0)
        except Exception:
            # Fallback for hackathon demo purposes if date parsing fails
            return 10 
