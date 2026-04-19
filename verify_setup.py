#!/usr/bin/env python3
"""
Comprehensive system verification and setup script.
Checks all components are properly configured for local operation.
"""

import sys
import os
import json
from pathlib import Path


def verify_imports():
    """Check all critical imports."""
    print("\n📦 Checking Imports...")
    imports = [
        ("app.services.data_loader", "DataLoader"),
        ("app.schemas.order", "Order"),
        ("app.schemas.customer", "Customer"),
        ("app.schemas.ticket", "Ticket"),
        ("app.core.orchestrator", "Orchestrator"),
        ("app.services.deterministic_engine", "DeterministicSupportEngine"),
        ("app.services.audit_logger", "AuditLogger"),
        ("config", "settings"),
    ]
    
    failed = []
    for module, cls in imports:
        try:
            exec(f"from {module} import {cls}")
            print(f"  ✅ {module}.{cls}")
        except Exception as e:
            print(f"  ❌ {module}.{cls}: {str(e)[:60]}")
            failed.append((module, cls))
    
    return len(failed) == 0


def verify_data_files():
    """Check all data files exist and are valid JSON."""
    print("\n📁 Checking Data Files...")
    data_dir = Path("data")
    files = ["customers.json", "orders.json", "tickets.json", "products.json"]
    
    all_valid = True
    for fname in files:
        fpath = data_dir / fname
        if not fpath.exists():
            print(f"  ❌ {fname}: NOT FOUND")
            all_valid = False
            continue
        
        try:
            with open(fpath) as f:
                data = json.load(f)
            count = len(data) if isinstance(data, list) else 1
            print(f"  ✅ {fname}: {count} records")
        except Exception as e:
            print(f"  ❌ {fname}: Invalid JSON - {str(e)[:40]}")
            all_valid = False
    
    return all_valid


def verify_schemas():
    """Check all schema definitions."""
    print("\n🏗️ Checking Schemas...")
    from app.schemas.order import Order
    from app.schemas.customer import Customer
    from app.schemas.ticket import Ticket
    
    schemas = [
        ("Order", Order, {"order_id": "ORD-001", "customer_id": "C-001"}),
        ("Customer", Customer, {"customer_id": "C-001", "first_name": "Test", "last_name": "User", "email": "test@example.com", "tier": "standard", "join_date": "2026-01-01"}),
        ("Ticket", Ticket, {"ticket_id": "T-001", "customer_id": "C-001", "subject": "Test", "body": "Test ticket", "created_at": "2026-01-01T00:00:00"}),
    ]
    
    all_valid = True
    for name, schema, sample in schemas:
        try:
            obj = schema(**sample)
            print(f"  ✅ {name} schema valid")
        except Exception as e:
            print(f"  ❌ {name} schema: {str(e)[:60]}")
            all_valid = False
    
    return all_valid


def verify_config():
    """Check configuration."""
    print("\n⚙️ Checking Configuration...")
    from config import settings
    
    required_attrs = [
        "TICKET_DATA", "CUSTOMER_DATA", "ORDER_DATA", "PRODUCT_DATA",
        "CONFIDENCE_THRESHOLD_ESCALATE", "MAX_REFUND_AUTO_APPROVE",
        "STANDARD_RETURN_DAYS"
    ]
    
    all_valid = True
    for attr in required_attrs:
        if hasattr(settings, attr):
            val = getattr(settings, attr)
            print(f"  ✅ {attr}: {str(val)[:40]}")
        else:
            print(f"  ❌ {attr}: NOT FOUND")
            all_valid = False
    
    return all_valid


def verify_deterministic_engine():
    """Check deterministic engine can process a sample ticket."""
    print("\n⚡ Testing Deterministic Engine...")
    import asyncio
    from app.services.deterministic_engine import DeterministicSupportEngine
    from app.services.audit_logger import AuditLogger
    
    try:
        audit = AuditLogger()
        engine = DeterministicSupportEngine(audit)
        
        sample_ticket = {
            "ticket_id": "T-VERIFY",
            "customer_id": "C-001",
            "order_id": "ORD-101",
            "subject": "Test ticket",
            "body": "Testing the system"
        }
        
        sample_customer = {
            "customer_id": "C-001",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Run the engine
        result = asyncio.run(engine.run(sample_ticket, sample_customer))
        
        if "status" in result and "reasoning" in result:
            print(f"  ✅ Engine works - Status: {result['status']}")
            print(f"     Confidence: {result.get('confidence_score', 0):.0%}")
            return True
        else:
            print(f"  ❌ Invalid result format: {list(result.keys())}")
            return False
            
    except Exception as e:
        print(f"  ❌ Engine error: {str(e)[:80]}")
        return False


def main():
    """Run all verifications."""
    print("\n" + "=" * 80)
    print("SHOPWAVE AUTONOMOUS AGENT - SYSTEM VERIFICATION")
    print("=" * 80)
    
    checks = [
        ("Imports", verify_imports),
        ("Data Files", verify_data_files),
        ("Schemas", verify_schemas),
        ("Configuration", verify_config),
        ("Deterministic Engine", verify_deterministic_engine),
    ]
    
    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"\n❌ {name} check failed: {str(e)[:80]}")
            results[name] = False
    
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL CHECKS PASSED - System is ready!")
        print("\nYou can now run:")
        print("  python demo_offline.py       # Quick demo (5 tickets)")
        print("  python run_offline.py        # Launch web UI")
    else:
        print("❌ SOME CHECKS FAILED - Fix issues above")
        print("\nCommon fixes:")
        print("  1. Ensure data/*.json files have required fields")
        print("  2. Check config/settings.py is properly set up")
        print("  3. Verify virtualenv is activated")
        print("  4. Run: pip install -r requirements.txt")
    print("=" * 80 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
