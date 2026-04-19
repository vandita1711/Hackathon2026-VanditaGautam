#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

async def test_complete_flow():
    try:
        print("=" * 60)
        print("COMPLETE SHOPWAVE SYSTEM TEST")
        print("=" * 60)

        # 1. Test configuration
        print("\n[1] Testing AutoGen Configuration...")
        from config.autogen_config import get_llm_config
        config = get_llm_config()
        assert config is not None, (
            "No LLM config — set GROQ_API_KEY (Groq) or OPENAI_API_KEY (OpenAI) in .env"
        )
        inner = config["config_list"][0]
        assert inner["model_info"]["function_calling"] is True
        assert inner["model_info"]["json_output"] is True
        print("[OK] AutoGen config: OK")

        # 2. Test agent creation
        print("\n[2] Testing AutoGen Agent Factory...")
        from app.agents.autogen_agents import AutoGenAgentFactory
        planner, executor, critic = AutoGenAgentFactory.create_agents("TEST-001")
        assert planner is not None, "Planner agent is None"
        assert executor is not None, "Executor agent is None"
        assert critic is not None, "Critic agent is None"
        print("[OK] Agent creation: OK")

        # 3. Test orchestrator with audit logging
        print("\n[3] Testing Orchestrator with Audit Logging...")
        from app.core.orchestrator import Orchestrator
        from config import settings

        # Clear audit log before test
        if os.path.exists(settings.AUDIT_LOG_PATH):
            os.remove(settings.AUDIT_LOG_PATH)

        orchestrator = Orchestrator()

        ticket = {
            "ticket_id": "TEST-FIXED-001",
            "customer_id": "test@example.com",
            "customer_email": "test@example.com",
            "subject": "Test refund request",
            "body": "Please refund my purchase",
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

        print("  Processing ticket...")
        result = await orchestrator.process_ticket(ticket, customer)
        print(f"[OK] Ticket processed: {result.get('status', 'unknown')}")

        # 4. Verify audit log was created
        print("\n[4] Verifying Audit Log...")
        assert os.path.exists(settings.AUDIT_LOG_PATH), "Audit log file not created"

        with open(settings.AUDIT_LOG_PATH, 'r') as f:
            logs = json.load(f)

        test_logs = [log for log in logs if log.get('ticket_id') == 'TEST-FIXED-001']
        print(f"  Found {len(test_logs)} audit entries for TEST-FIXED-001")
        assert len(test_logs) > 0, "No audit logs found for ticket"

        # Check for key events
        event_types = set(log['event_type'] for log in test_logs)
        print(f"  Event types: {event_types}")
        assert 'ticket_received' in event_types, "No ticket_received event"
        print("[OK] Audit log: OK")

        # 5. Test UI integration
        print("\n[5] Testing UI Integration...")
        from ui_app import ShopWaveUI

        ui = ShopWaveUI()
        ui.results = [
            {
                'ticket_id': 'TEST-FIXED-001',
                'status': 'resolved',
                'confidence_score': 0.85,
                'reasoning': 'Test resolution'
            }
        ]

        # Simulate Gradio select event
        class MockSelectEvent:
            """Matches gr.SelectData fields used by get_ticket_details."""
            selected = True
            row_value = [0, "TEST-FIXED-001", "RESOLVED", "85%", "Test resolution..."]
            index = (0, 0)

        trace = ui.get_ticket_details(MockSelectEvent())

        assert 'TEST-FIXED-001' in trace, "Ticket ID not in trace"
        assert len(trace) > 0, "No trace data returned"
        print("[OK] UI integration: OK")

        print("\n" + "=" * 60)
        print("SUCCESS: ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSystem is ready to use. Run: python ui_app.py")

    except AssertionError as e:
        print(f"\nERROR ASSERTION: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\nERROR TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_complete_flow())
    sys.exit(0 if success else 1)