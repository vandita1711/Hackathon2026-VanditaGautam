import asyncio
from app.tools.tool_registry import registry
from app.services.retry_handler import RetryHandler
from app.core.logger import logger

class Executor:
    """Agent responsible for executing tool calls and collecting results."""
    
    async def execute_plan(self, plan: list) -> list:
        results = []
        for step in plan:
            tool_name = step.get("tool_name")
            params = step.get("parameters", {})
            
            logger.info(f"Executing tool: {tool_name} with params: {params}")
            
            try:
                # Use the registry to call the actual Python function with retry
                result = await RetryHandler.execute_with_retry(registry.call, tool_name, **params)
                results.append({
                    "tool": tool_name,
                    "parameters": params,
                    "output": result,
                    "status": "success"
                })
            except Exception as e:
                logger.error(f"Tool {tool_name} failed after retries: {str(e)}")
                results.append({
                    "tool": tool_name,
                    "parameters": params,
                    "output": str(e),
                    "status": "error"
                })
                
        return results
