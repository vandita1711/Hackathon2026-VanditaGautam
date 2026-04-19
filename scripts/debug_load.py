import json
from app.services.data_loader import DataLoader
from app.schemas.ticket import Ticket
from app.schemas.customer import Customer
from config import settings

def debug_load():
    print(f"Checking {settings.TICKET_DATA}")
    with open(settings.TICKET_DATA, 'r') as f:
        data = json.load(f)
        print(f"JSON has {len(data)} items")
        print(f"Sample item: {data[0]}")
    
    tickets = DataLoader.load_collection(str(settings.TICKET_DATA), Ticket)
    print(f"DataLoader loaded {len(tickets)} Ticket objects")
    
    customers = DataLoader.load_collection(str(settings.CUSTOMER_DATA), Customer)
    print(f"DataLoader loaded {len(customers)} Customer objects")

if __name__ == "__main__":
    debug_load()
