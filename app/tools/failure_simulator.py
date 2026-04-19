from app.core.logger import logger
from .tool_registry import registry

@registry.register(description="Simulate a system check for internal tools. Use for diagnostics.")
def simulate_system_check(system_name: str) -> str:
    logger.info(f"Simulating system check for: {system_name}")
    return f"Status: {system_name} is operational."
