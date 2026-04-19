import asyncio
from app.core.orchestrator import Orchestrator
from app.core.logger import logger
from typing import List, Dict

async def process_tickets_batch(tickets: List[Dict], customers_map: Dict) -> List[Dict]:
    """
    Process a batch of tickets concurrently using AutoGen orchestrator.
    """
    orchestrator = Orchestrator()
    tasks = []
    
    for ticket in tickets:
        customer_id = ticket.get("customer_id") or ticket.get("customer_email")
        customer = customers_map.get(customer_id, {})
        
        # Create a task for each ticket to run concurrently
        tasks.append(orchestrator.process_ticket(ticket, customer))
    
    if not tasks:
        logger.warning("No tickets to process.")
        return []
        
    logger.info(f"Dispatching {len(tasks)} tickets for concurrent processing...")

    results = await asyncio.gather(
        *[asyncio.wait_for(task, timeout=30) for task in tasks],
        return_exceptions=True
    )
    
    # ✅ FIX: this block MUST be inside function
    final_results = []

    for res in results:
        if isinstance(res, Exception):
            final_results.append({
                "status": "error",
                "confidence_score": 0,
                "reasoning": str(res)
            })
        else:
            final_results.append(res)

    return final_results
