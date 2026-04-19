import json
from nexttoken import NextToken
from config import settings, prompts
from app.tools.tool_registry import registry

client = NextToken()

class Planner:
    """Agent responsible for creating a step-by-step resolution plan."""
    
    async def create_plan(self, ticket_data: dict, customer_data: dict) -> list:
        context = f"Ticket: {json.dumps(ticket_data)}\nCustomer: {json.dumps(customer_data)}"
        
        # Get available tool schemas from registry
        tool_schemas = registry.get_tool_schemas()
        
        response = client.chat.completions.create(
            model=settings.PLANNER_MODEL,
            messages=[
                {"role": "system", "content": prompts.PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Create a resolution plan for this ticket:\n{context}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        try:
            plan_data = json.loads(content)
            # Support both {"plan": [...]} and [...]
            return plan_data.get("plan", plan_data) if isinstance(plan_data, dict) else plan_data
        except json.JSONDecodeError:
            return []
