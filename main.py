"""ASGI entrypoint when uvicorn is started from the repo root."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

_backend_main = _backend_dir / "main.py"
_spec = spec_from_file_location("trialsense_backend_main", _backend_main)
_module = module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_module)

app = _module.app
