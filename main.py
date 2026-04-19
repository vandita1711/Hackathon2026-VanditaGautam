
import asyncio
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from app.core.logger import logger
from pipelines.process_tickets import process_tickets_batch
from app.services.data_loader import DataLoader
from config import settings
from app.schemas.ticket import Ticket
from app.schemas.customer import Customer

# Import tool modules to register them
from app.tools import knowledge_tools, order_tools, refund_tools, communication_tools, failure_simulator

async def main():
    parser = argparse.ArgumentParser(description="ShopWave Autonomous Support Agent CLI")
    parser.add_argument("--demo", action="store_true", help="Run the full hackathon demo suite")
    parser.add_argument("--ticket", type=str, help="Process a single ticket ID")
    args = parser.parse_args()

    logger.info("Initializing ShopWave System...")

    # Load Data
    all_tickets = DataLoader.load_collection(str(settings.TICKET_DATA), Ticket)
    all_customers = DataLoader.load_collection(str(settings.CUSTOMER_DATA), Customer)
    customers_map = {}
    for customer in all_customers:
        customer_data = customer.model_dump()
        customers_map[customer.customer_id] = customer_data
        if customer.email:
            customers_map[customer.email] = customer_data

    if args.demo:
        logger.info("Running Hackathon Demo Suite...")
        # Select first 5 tickets for the demo to save time/cost
        tickets_to_process = all_tickets[:5]
        results = await process_tickets_batch([t.model_dump(by_alias=True) for t in tickets_to_process], customers_map)
        print("\n--- DEMO RESULTS ---")
        for res in results:
            print(f"Ticket {res.get('ticket_id')}: {res.get('status').upper()} - {res.get('reasoning')[:100]}...")
        print(f"\nAudit logs saved to: {settings.AUDIT_LOG_PATH}")
    
    elif args.ticket:
        target = next((t for t in all_tickets if t.ticket_id == args.ticket), None)
        if not target:
            logger.error(f"Ticket {args.ticket} not found.")
            return
        results = await process_tickets_batch([target.model_dump()], customers_map)
        print(f"\nResult for {args.ticket}:", results[0])
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
