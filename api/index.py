"""Vercel serverless entrypoint for the FastAPI backend."""

import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_backend_dir))

from main import app  # noqa: E402, F401
