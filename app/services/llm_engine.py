import json
import os
from typing import Any, Dict

from config import prompts, settings
from config.autogen_config import get_llm_config
from app.core.logger import logger

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - environment dependent
    OpenAI = None


class LLMSupportEngine:
    """Optional Groq-backed review layer on top of deterministic tool execution."""

    def __init__(self, audit_logger):
        self.audit = audit_logger

    @classmethod
    def is_available(cls) -> bool:
        return bool(settings.ENABLE_LLM and get_llm_config() is not None and OpenAI is not None)

    async def evaluate_resolution(
        self,
        ticket: Dict[str, Any],
        customer: Dict[str, Any],
        tool_results: list,
        draft_resolution: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not self.is_available():
            return draft_resolution

        messages = [
            {
                "role": "system",
                "content": (
                    prompts.CRITIC_SYSTEM_PROMPT
                    + "\nYou are reviewing a deterministic support decision."
                    + " Preserve hard business rules. Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "ticket": ticket,
                        "customer": customer,
                        "tool_results": tool_results,
                        "draft_resolution": draft_resolution,
                    }
                ),
            },
        ]

        try:
            cfg = get_llm_config()
            if not cfg:
                return draft_resolution
            inner = cfg["config_list"][0]

            client = OpenAI(api_key=inner["api_key"], base_url=inner["base_url"])

            response = client.chat.completions.create(
                model=inner["model"],
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)

            merged = {
                "ticket_id": draft_resolution["ticket_id"],
                "status": parsed.get("status", draft_resolution["status"]),
                "reasoning": parsed.get("reasoning", draft_resolution["reasoning"]),
                "confidence_score": float(
                    parsed.get("confidence_score", draft_resolution["confidence_score"])
                ),
                "final_message": parsed.get(
                    "final_message", draft_resolution["final_message"]
                ),
                "escalation_team": parsed.get(
                    "escalation_team", draft_resolution.get("escalation_team")
                ),
                "llm_enhanced": True,
            }

            self.audit.log_event(
                draft_resolution["ticket_id"],
                "llm_review_completed",
                {"response": merged},
            )

            return merged

        except Exception as exc:
            logger.warning(
                f"LLM review failed, falling back to deterministic result: {exc}"
            )

            self.audit.log_event(
                draft_resolution["ticket_id"],
                "llm_review_failed",
                {"error": str(exc)},
            )

            return draft_resolution
