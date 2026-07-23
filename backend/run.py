"""
Uvicorn launcher for the Ephemeral Intent Synthesis System.

Run from the backend/ directory:

    python run.py

This script explicitly adds the backend/ directory to sys.path before
importing uvicorn, which prevents the "No module named 'app'" error that
occurs on Windows when uvicorn --reload spawns a subprocess via
multiprocessing and the working directory is not on sys.path.
"""

import os
import sys
from pathlib import Path

# Ensure the backend/ directory is on sys.path so `import app` works
# both in the main process and in the reload subprocess.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load .env before uvicorn touches any config
from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

import uvicorn

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(BACKEND_DIR)],   # reload subprocess inherits this path
        app_dir=str(BACKEND_DIR),         # tells uvicorn where to find `app`
        log_level=log_level,
    )
