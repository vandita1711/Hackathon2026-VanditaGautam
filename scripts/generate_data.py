import json
import os
from datetime import datetime, timedelta

def generate_mock_data():
    os.makedirs("data", exist_ok=True)
    
    # 1. Customers
    customers = [
        {"customer_id": "C-001", "first_name": "Aditya", "last_name": "Sharma", "email": "aditya@example.com", "tier": "VIP", "join_date": "2023-01-01"},
        {"customer_id": "C-002", "first_name": "Sarah", "last_name": "Jones", "email": "sarah@example.com", "tier": "Standard", "join_date": "2024-05-10"}
    ]
    
    # 2. Orders
    orders = [
        {
            "order_id": "ORD-101", "customer_id": "C-001", "order_date": (datetime.now() - timedelta(days=10)).isoformat(),
            "status": "delivered", "total_amount": 150.0, "items": [{"product_id": "P-1", "name": "Wireless Mouse", "category": "electronics accessories", "price": 150.0, "quantity": 1}]
        },
        {
            "order_id": "ORD-102", "customer_id": "C-002", "order_date": (datetime.now() - timedelta(days=40)).isoformat(),
            "status": "delivered", "total_amount": 300.0, "items": [{"product_id": "P-2", "name": "Premium Headphones", "category": "high-value electronics", "price": 300.0, "quantity": 1}]
        }
    ]
    
    # 3. Tickets
    tickets = [
        {"ticket_id": "T-001", "customer_id": "C-001", "subject": "Refund Request", "description": "My mouse is double clicking. I want a refund.", "order_id": "ORD-101", "created_at": datetime.now().isoformat()},
        {"ticket_id": "T-002", "customer_id": "C-002", "subject": "Help with Headphones", "description": "I bought these headphones 40 days ago and they broke. I need a refund.", "order_id": "ORD-102", "created_at": datetime.now().isoformat()}
    ]
    
    # 4. Products
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
    with open("data/tickets.json", "w") as f: json.dump(tickets, f, indent=4)
    with open("data/products.json", "w") as f: json.dump(products, f, indent=4)
    
    print("Mock data generated successfully.")

if __name__ == "__main__":
    generate_mock_data()
