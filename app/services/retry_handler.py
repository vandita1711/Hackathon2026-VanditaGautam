import asyncio
from typing import Callable, Any, TypeVar
from app.core.logger import logger

T = TypeVar("T")

class RetryHandler:
    """Handles retries for flaky tool calls or LLM responses."""
    
    @staticmethod
    async def execute_with_retry(
        func: Callable[..., Any], 
        *args, 
        max_retries: int = 3, 
        base_delay: float = 1.0, 
        **kwargs
    ) -> Any:
        last_exception = None
        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        logger.error(f"All {max_retries} attempts failed.")
        raise last_exception
