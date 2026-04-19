from typing import Optional, Dict, Any
from app.services.data_loader import DataLoader
from app.schemas.order import Order
from app.schemas.customer import Customer
from config import settings
from .tool_registry import registry

@registry.register(description="Get details for a specific order by ID.")
def get_order_details(order_id: str) -> str:
    order = DataLoader.find_by_id(str(settings.ORDER_DATA), Order, "order_id", order_id)
    if not order:
        return f"Order {order_id} not found."
    return order.model_dump_json()

@registry.register(description="Get a customer's profile by their customer ID or email.")
def get_customer_profile(customer_id: str) -> str:
    customer = DataLoader.find_by_id(str(settings.CUSTOMER_DATA), Customer, "customer_id", customer_id)
    if not customer:
        return f"Customer {customer_id} not found."
    return customer.model_dump_json()

@registry.register(description="Find recent orders for a customer when the ticket does not include an order ID.")
def get_customer_orders(customer_id: str) -> str:
    orders = DataLoader.find_many_by_field(str(settings.ORDER_DATA), Order, "customer_id", customer_id)
    if not orders:
        return f"No orders found for customer {customer_id}."
    return "[" + ", ".join(order.model_dump_json() for order in orders[:5]) + "]"

@registry.register(description="Check if an order is eligible for cancellation.")
def check_cancellation_eligibility(order_id: str) -> str:
    order = DataLoader.find_by_id(str(settings.ORDER_DATA), Order, "order_id", order_id)
    if not order:
        return f"Order {order_id} not found."
    
    if order.status == "processing":
        return "Eligible: Order is still processing and can be cancelled."
    return f"Ineligible: Order status is '{order.status}'."

@registry.register(description="Get current shipping or delivery status for an order.")
def get_shipping_status(order_id: str) -> str:
    order = DataLoader.find_by_id(str(settings.ORDER_DATA), Order, "order_id", order_id)
    if not order:
        return f"Order {order_id} not found."

    if order.status == "processing":
        return f"Order {order_id} is still being prepared for shipment."
    if order.status == "shipped":
        tracking = order.tracking_number or "tracking pending"
        return f"Order {order_id} is in transit. Tracking: {tracking}."
    if order.status == "delivered":
        return f"Order {order_id} was delivered to {order.shipping_address}."
    if order.status == "cancelled":
        return f"Order {order_id} has already been cancelled."
    return f"Order {order_id} is currently in status '{order.status}'."

@registry.register(description="Retrieve product details. Use for category or warranty checks.")
def get_product_info(product_id: str) -> str:
    products = DataLoader._load_raw(str(settings.PRODUCT_DATA))
    for p in products:
        if p.get("product_id") == product_id:
            return str(p)
    return f"Product {product_id} not found."
