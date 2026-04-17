from __future__ import annotations

import os
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent / "backend"
_backend_str = str(_BACKEND)
if _backend_str not in sys.path:
    sys.path.insert(0, _backend_str)
os.environ["PYTHONPATH"] = _backend_str + os.pathsep + os.environ.get("PYTHONPATH", "")

_DEFAULT_PORT = 8765

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("EMR_PORT", str(_DEFAULT_PORT)))
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
        reload_dirs=[_backend_str],
    )
