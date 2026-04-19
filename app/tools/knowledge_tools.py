import os
from config import settings
from .tool_registry import registry

@registry.register(description="Search the company policy knowledge base.")
def get_policy_info(keywords: str) -> str:
    policy_path = os.path.join(settings.KNOWLEDGE_BASE_DIR, "policies.txt")
    if not os.path.exists(policy_path):
        return "Policy database not found."
        
    with open(policy_path, "r") as f:
        content = f.read()
        
    # Simple keyword-based extraction
    relevant_lines = []
    keyword_list = [k.strip().lower() for k in keywords.split(",")]
    
    for line in content.split("\n"):
        if any(k in line.lower() for k in keyword_list):
            relevant_lines.append(line)
            
    if not relevant_lines:
        return f"No specific policy found for '{keywords}'. Escalation recommended."
        
    return "\n".join(relevant_lines)
