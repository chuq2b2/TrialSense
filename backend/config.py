import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "synthea"
SQLITE_PATH = DATA_DIR / "trialsense.db"

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env.local")
load_dotenv(PROJECT_ROOT / "frontend" / ".env")

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()

if DB_BACKEND == "postgresql":
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://trialsense:trialsense@localhost:5432/trialsense",
    )
else:
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
NEBIUS_BASE_URL = os.getenv(
    "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
)
NEBIUS_MODEL = os.getenv(
    "NEBIUS_MODEL", "meta-llama/Llama-3.3-70B-Instruct"
)
NEBIUS_SCORING_MODEL = os.getenv("NEBIUS_SCORING_MODEL", "Qwen/Qwen3-32B")

# Local parsing + heuristics are the default; enable LLM paths only when needed.
USE_LLM_CRITERIA = os.getenv("USE_LLM_CRITERIA", "false").lower() in {
    "1",
    "true",
    "yes",
}
USE_LLM_SCORING = os.getenv("USE_LLM_SCORING", "false").lower() in {
    "1",
    "true",
    "yes",
}
