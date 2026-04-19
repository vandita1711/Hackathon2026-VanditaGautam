import os
from config import settings


def get_llm_config():
    """Returns AutoGen-compatible LLM config.

    Keys must match the API base URL: a Groq key only works with Groq's base URL;
    an OpenAI key only with OpenAI's base URL. Mixing them produces 401 Invalid API Key.
    """

    groq_key = settings.GROQ_API_KEY
    print("DEBUG GROQ KEY:", groq_key)
    openai_key = settings.OPENAI_API_KEY

    if groq_key:
        base_url = (os.getenv("GROQ_BASE_URL") or settings.AUTOGEN_BASE_URL or "https://api.groq.com/openai/v1").strip()
        return {
            "provider": "groq",
            "config_list": [
                {
                    "model": settings.AUTOGEN_MODEL,
                    "api_key": groq_key,
                    "base_url": base_url,
                    "model_info": {
                        "family": "llama",
                        "vision": False,
                        "max_tokens": 8192,
                        "context_window": 8192,
                        "function_calling": True,
                        "json_output": True,
                        "structured_output": True,
                    },
                }
            ],
            "temperature": 0,
            "cache_seed": None,
        }

    if openai_key:
        base_url = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip()
        model = settings.AUTOGEN_OPENAI_MODEL
        return {
            "provider": "openai",
            "config_list": [
                {
                    "model": model,
                    "api_key": openai_key,
                    "base_url": base_url,
                    "model_info": {
                        "family": "gpt",
                        "vision": False,
                        "max_tokens": 8192,
                        "context_window": 128000,
                        "function_calling": True,
                        "json_output": True,
                        "structured_output": True,
                    },
                }
            ],
            "temperature": 0,
            "cache_seed": None,
        }

    return None
