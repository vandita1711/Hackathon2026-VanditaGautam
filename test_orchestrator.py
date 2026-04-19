#!/usr/bin/env python3

import asyncio
import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

async def test_orchestrator():
    try:
        print("Testing orchestrator and audit logging...")

        from app.core.orchestrator import Orchestrator

        # Create test data
        ticket = {
            "ticket_id": "TEST-001",
            "customer_id": "test@example.com",
            "subject": "Test ticket",
            "body": "This is a test ticket for refund",
            "status": "open",
            "priority": "medium"
        }

        customer = {
            "customer_id": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "tier": "Standard"
        }

        # Create orchestrator and process
        orchestrator = Orchestrator()
        print("Processing ticket...")
        result = await orchestrator.process_ticket(ticket, customer)
        print(f"Result: {result}")

        # Check if audit log was written
        audit_path = "artifacts/audit_log.json"
        if os.path.exists(audit_path):
            with open(audit_path, 'r') as f:
                logs = json.load(f)

            # Get recent logs for this ticket
            recent_logs = [log for log in logs if log.get('ticket_id') == 'TEST-001']
            print(f"Found {len(recent_logs)} audit log entries for TEST-001")

            for log in recent_logs[-5:]:  # Show last 5
                print(f"  {log['timestamp']} - {log['event_type']}")
        else:
            print("Audit log file does not exist")

        print("Orchestrator test completed!")

    except Exception as e:
        print(f"Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orchestrator())