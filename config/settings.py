import os
from pathlib import Path

# Lightweight .env loader so local keys do not need to be hardcoded.
def _load_dotenv():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()

# Project Root
BASE_DIR = Path(__file__).resolve().parent.parent

# Data Directories
DATA_DIR = BASE_DIR / "data"
TICKET_DATA = DATA_DIR / "tickets.json"
CUSTOMER_DATA = DATA_DIR / "customers.json"
ORDER_DATA = DATA_DIR / "orders.json"
PRODUCT_DATA = DATA_DIR / "products.json"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"

# Artifacts
ARTIFACTS_DIR = BASE_DIR / "artifacts"
AUDIT_LOG_PATH = ARTIFACTS_DIR / "audit_log.json"

# Business Rules / Constraints
MAX_REFUND_AUTO_APPROVE = 200.0
STANDARD_RETURN_DAYS = 30
ELECTRONICS_ACCESSORIES_RETURN_DAYS = 60
HIGH_VALUE_ELECTRONICS_RETURN_DAYS = 15
CONFIDENCE_THRESHOLD_ESCALATE = 0.6

# LLM Settings
# Default models based on LLM-Calling Instructions
PLANNER_MODEL = "gemini-3-flash-preview"
EXECUTOR_MODEL = "gemini-3-flash-preview"
CRITIC_MODEL = "gemini-3.1-pro-preview"

# Groq / AutoGen Settings (values are stripped — trailing spaces in .env break auth)
def _env_strip(key: str) -> str | None:
    v = os.getenv(key)
    if v is None:
        return None
    v = v.strip()
    return v if v else None


GROQ_API_KEY = _env_strip("GROQ_API_KEY")
print("LOADED GROQ KEY:", GROQ_API_KEY)
OPENAI_API_KEY = _env_strip("OPENAI_API_KEY")
# Default Groq endpoint; OpenAI uses OPENAI_BASE_URL or https://api.openai.com/v1 (see autogen_config)
AUTOGEN_MODEL = "llama-3.3-70b-versatile"  # Used with Groq
AUTOGEN_BASE_URL = (os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1").strip()
AUTOGEN_OPENAI_MODEL = (os.getenv("AUTOGEN_OPENAI_MODEL") or "gpt-4o-mini").strip()
ENABLE_LLM = os.getenv("ENABLE_LLM", "true").lower() in {"1", "true", "yes", "on"}

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
