import os
from config import settings
from config.autogen_config import get_llm_config

def debug_config():
    print(f"GROQ_API_KEY set: {bool(settings.GROQ_API_KEY)}")
    config = get_llm_config()
    print(f"Config type: {type(config)}")
    print(f"Config keys: {config.keys()}")
    print(f"Config content: {config}")

if __name__ == "__main__":
    debug_config()
