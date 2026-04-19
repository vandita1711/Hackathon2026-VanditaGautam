import json
import os
from datetime import datetime, timedelta

def generate_aligned_mock_data():
    os.makedirs("data", exist_ok=True)
    
    # 1. Customers (Aligned with tickets)
    customers = [
        {"customer_id": "alice.turner@email.com", "first_name": "Alice", "last_name": "Turner", "email": "alice.turner@email.com", "tier": "Standard", "join_date": "2023-01-01"},
        {"customer_id": "bob.mendes@email.com", "first_name": "Bob", "last_name": "Mendes", "email": "bob.mendes@email.com", "tier": "Standard", "join_date": "2023-01-01"},
        {"customer_id": "carol.nguyen@email.com", "first_name": "Carol", "last_name": "Nguyen", "email": "carol.nguyen@email.com", "tier": "Standard", "join_date": "2023-01-01"},
        {"customer_id": "david.park@email.com", "first_name": "David", "last_name": "Park", "email": "david.park@email.com", "tier": "Standard", "join_date": "2023-01-01"},
        {"customer_id": "emma.collins@email.com", "first_name": "Emma", "last_name": "Collins", "email": "emma.collins@email.com", "tier": "VIP", "join_date": "2023-01-01"}
    ]
    
    # 2. Orders (Aligned with tickets)
    orders = [
        {
            "order_id": "ORD-1001", "customer_id": "alice.turner@email.com", "order_date": (datetime.now() - timedelta(days=20)).isoformat(),
            "status": "delivered", "total_amount": 80.0, "items": [{"product_id": "P-H", "name": "Headphones", "category": "electronics accessories", "price": 80.0, "quantity": 1}]
        },
        {
            "order_id": "ORD-1002", "customer_id": "bob.mendes@email.com", "order_date": (datetime.now() - timedelta(days=25)).isoformat(),
            "status": "delivered", "total_amount": 250.0, "items": [{"product_id": "P-W", "name": "Smart Watch", "category": "high-value electronics", "price": 250.0, "quantity": 1}]
        },
        {
            "order_id": "ORD-1003", "customer_id": "carol.nguyen@email.com", "order_date": (datetime.now() - timedelta(days=35)).isoformat(),
            "status": "delivered", "total_amount": 120.0, "items": [{"product_id": "P-C", "name": "Coffee Maker", "category": "electronics", "price": 120.0, "quantity": 1}]
        },
        {
            "order_id": "ORD-1004", "customer_id": "david.park@email.com", "order_date": (datetime.now() - timedelta(days=5)).isoformat(),
            "status": "delivered", "total_amount": 90.0, "items": [{"product_id": "P-S", "name": "Running Shoes", "category": "footwear", "price": 90.0, "quantity": 1}]
        },
        {
            "order_id": "ORD-1005", "customer_id": "emma.collins@email.com", "order_date": (datetime.now() - timedelta(days=100)).isoformat(),
            "status": "delivered", "total_amount": 150.0, "items": [{"product_id": "P-B", "name": "Bluetooth Speakers", "category": "electronics accessories", "price": 150.0, "quantity": 2}]
        }
    products = [
        {
            "product_id": "P-H",
            "name": "Headphones",
            "category": "electronics accessories",
            "price": 80.0,
            "description": "Wireless noise-cancelling headphones",
            "warranty_months": 12,
            "return_window_days": 60
        },
        {
            "product_id": "P-W",
            "name": "Smart Watch",
            "category": "high-value electronics",
            "price": 250.0,
            "description": "Fitness tracking smart watch with heart rate monitor",
            "warranty_months": 24,
            "return_window_days": 15
        },
        {
            "product_id": "P-C",
            "name": "Coffee Maker",
            "category": "electronics",
            "price": 120.0,
            "description": "Programmable coffee maker with thermal carafe",
            "warranty_months": 12,
            "return_window_days": 30
        },
        {
            "product_id": "P-S",
            "name": "Running Shoes",
            "category": "footwear",
            "price": 90.0,
            "description": "Lightweight running shoes with cushioning",
            "warranty_months": 6,
            "return_window_days": 30
        },
        {
            "product_id": "P-B",
            "name": "Bluetooth Speakers",
            "category": "electronics accessories",
            "price": 75.0,
            "description": "Portable wireless Bluetooth speakers",
            "warranty_months": 12,
            "return_window_days": 60
        }
    ]

    with open("data/customers.json", "w") as f: json.dump(customers, f, indent=4)
    with open("data/orders.json", "w") as f: json.dump(orders, f, indent=4)
    with open("data/products.json", "w") as f: json.dump(products, f, indent=4)
    
    print("Mock database aligned with uploaded tickets.")

if __name__ == "__main__":
    generate_aligned_mock_data()
