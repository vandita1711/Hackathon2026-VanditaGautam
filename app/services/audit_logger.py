import json
import os
from datetime import datetime
from config import settings
from app.core.logger import logger

class AuditLogger:
    """Logs all agent decisions and tool outputs to a persistent JSON file."""
    
    @staticmethod
    def log_event(ticket_id: str, event_type: str, data: dict):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "event_type": event_type,
            "data": data
        }
        
        # Ensure directory exists
        os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
        
        # Read existing logs or start new list
        logs = []
        if os.path.exists(settings.AUDIT_LOG_PATH):
            try:
                with open(settings.AUDIT_LOG_PATH, "r") as f:
                    logs = json.load(f)
            except Exception:
                logs = []
        
        logs.append(log_entry)
        
        with open(settings.AUDIT_LOG_PATH, "w") as f:
            json.dump(logs, f, indent=2)
            
        logger.debug(f"Audit log updated for ticket {ticket_id}: {event_type}")
