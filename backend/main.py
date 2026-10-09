"""
MetroFlowNet Backend Application Root Entrypoint
For Render and other cloud platforms where startCommand is `uvicorn main:app --host 0.0.0.0 --port $PORT`
or `python main.py`.
"""
from __future__ import annotations

import os
import uvicorn

from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
