import inspect
import functools
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel
try:
    from autogen_core.tools import FunctionTool
except Exception:
    FunctionTool = None

class ToolRegistry:
    """Registry to manage and describe tools for the LLM."""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.schemas: List[Dict[str, Any]] = []
        self._modules_loaded = False

    def _ensure_modules_loaded(self):
        if self._modules_loaded:
            return
        import app.tools.knowledge_tools
        import app.tools.order_tools
        import app.tools.refund_tools
        import app.tools.communication_tools
        import app.tools.failure_simulator

        self._modules_loaded = True

    def register(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a tool function."""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or "No description provided."
            self.tools[tool_name] = func
            self.schemas.append(
                {
                    "name": tool_name,
                    "description": tool_description.strip(),
                    "parameters": list(inspect.signature(func).parameters.keys()),
                }
            )
            return func
        return decorator

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        self._ensure_modules_loaded()
        return self.schemas

    def get_autogen_tools(self) -> List[Any]:
        """Converts registered functions to AutoGen 0.7+ FunctionTool objects."""
        if FunctionTool is None:
            return []

        self._ensure_modules_loaded()
        
        autogen_tools = []
        for name, func in self.tools.items():
            description = func.__doc__ or f"Tool: {name}"
            autogen_tools.append(FunctionTool(func, description=description.strip(), name=name))
        return autogen_tools

    def call(self, name: str, **kwargs) -> Any:
        self._ensure_modules_loaded()
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found in registry.")
        return self.tools[name](**kwargs)

# Global registry instance
registry = ToolRegistry()
