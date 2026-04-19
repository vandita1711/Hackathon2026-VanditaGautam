import json
from nexttoken import NextToken
from config import settings, prompts

client = NextToken()

class Critic:
    """Agent responsible for validating compliance, confidence, and safety."""
    
    async def evaluate_resolution(self, ticket_data: dict, plan_results: list) -> dict:
        context = {
            "ticket": ticket_data,
            "execution_results": plan_results
        }
        
        response = client.chat.completions.create(
            model=settings.CRITIC_MODEL,
            messages=[
                {"role": "system", "content": prompts.CRITIC_SYSTEM_PROMPT},
                {"role": "user", "content": f"Evaluate the following support resolution context:\n{json.dumps(context)}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=8000
        )
        
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "status": "escalate",
                "confidence_score": 0.0,
                "reasoning": "Failed to parse Critic evaluation output.",
                "final_message": "I am having trouble processing your request. Escalating to a human."
            }
