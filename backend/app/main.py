"""
FastAPI Main Application Entry Point
Ephemeral Intent Synthesis System
"""

# Load .env before anything else so every os.getenv() call sees the values
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import threading
from datetime import datetime
from typing import Dict, Any
import os

from app.api.websocket import websocket_endpoint
from app.api.pipeline import get_rag_engine, is_rag_ready, get_lifecycle_manager
from app.services.video_generator import VideoGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons — created once, reused everywhere
# ---------------------------------------------------------------------------

_video_generator: VideoGenerator | None = None


def get_video_generator() -> VideoGenerator:
    global _video_generator
    if _video_generator is None:
        _video_generator = VideoGenerator()
    return _video_generator


# ---------------------------------------------------------------------------
# Startup warm-up
# ---------------------------------------------------------------------------

def _warm_up_services() -> None:
    """Pre-load heavy services in a background thread so the server accepts
    connections immediately.  The first WS client that arrives before warm-up
    finishes gets a friendly 'warming_up' status message.

    NOTE: do NOT start async tasks here — there is no event loop in this thread.
    Async startup (LifecycleManager monitoring) happens in the lifespan coroutine.
    """
    try:
        logger.info("⏳ Pre-loading RAG engine…")
        get_rag_engine()
        logger.info("✅ RAG engine ready")
    except Exception as exc:
        logger.error(f"⚠️  RAG engine warm-up failed: {exc}")

    try:
        get_video_generator()
        logger.info("✅ VideoGenerator ready")
    except Exception as exc:
        logger.error(f"⚠️  VideoGenerator warm-up failed: {exc}")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Ephemeral Intent Synthesis System…")

    # Heavy sync work (embedding model, ChromaDB) runs in a thread so the
    # server starts accepting requests immediately.
    t = threading.Thread(target=_warm_up_services, daemon=True)
    t.start()

    # Async startup — must happen here where the event loop is running.
    try:
        lm = get_lifecycle_manager()
        lm.start_monitoring()
        logger.info("✅ LifecycleManager monitoring started")
    except Exception as exc:
        logger.error(f"⚠️  LifecycleManager startup failed: {exc}")

    yield

    logger.info("🛑 Shutting down…")
    try:
        get_lifecycle_manager().stop_monitoring()
    except Exception:
        pass


app = FastAPI(
    title="Ephemeral Intent Synthesis System",
    description="AI-powered biometric-adaptive educational interface system",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    lifespan=lifespan,
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """Health check — uses pre-initialised singletons, no extra work."""
    vg = get_video_generator()
    video_status = (
        "ready" if vg.is_ready()
        else "disabled" if not vg.enabled
        else "not_configured"
    )
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "components": {
            "api": "operational",
            "rag_engine": "ready" if is_rag_ready() else "warming_up",
            "video_generator": video_status,
            "lifecycle_manager": "monitoring",
        },
    }


@app.get("/", tags=["System"])
async def root() -> Dict[str, Any]:
    return {
        "name": "Ephemeral Intent Synthesis System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "websocket": "/ws/{session_id}",
    }


@app.get("/api/v1/system/info", tags=["System"])
async def system_info() -> Dict[str, Any]:
    lm = get_lifecycle_manager()
    return {
        "system": {
            "name": "Ephemeral Intent Synthesis System",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
        },
        "runtime": {
            "rag_ready": is_rag_ready(),
            "active_sessions": lm.get_active_sessions_count(),
            "ollama_model": os.getenv("OLLAMA_MODEL", "phi3:mini"),
            "video_enabled": os.getenv("VIDEO_ENABLED", "false").lower() == "true",
        },
    }


# ---------------------------------------------------------------------------
# Session endpoints (backed by LifecycleManager)
# ---------------------------------------------------------------------------

@app.get("/api/v1/sessions", tags=["Sessions"])
async def list_sessions() -> Dict[str, Any]:
    """Return all active sessions."""
    lm = get_lifecycle_manager()
    return {"sessions": lm.get_all_sessions(), "count": lm.get_active_sessions_count()}


@app.get("/api/v1/sessions/{session_id}", tags=["Sessions"])
async def get_session(session_id: str) -> Dict[str, Any]:
    """Return a single session by ID."""
    lm = get_lifecycle_manager()
    session = lm.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@app.delete("/api/v1/sessions/{session_id}", tags=["Sessions"])
async def terminate_session(session_id: str) -> Dict[str, Any]:
    """Manually terminate a session and free its resources."""
    lm = get_lifecycle_manager()
    success = lm.terminate_session(session_id, reason="api_request")
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"terminated": True, "session_id": session_id}


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code, "timestamp": datetime.utcnow().isoformat()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An error occurred",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/{session_id}")
async def websocket_route(websocket: WebSocket, session_id: str):
    """
    Real-time pipeline endpoint.

    Message types:
      full_pipeline       — complete biometric → knowledge → UI pipeline
      biometric_analysis  — biometric step only
      knowledge_query     — knowledge step only
      ping                — keepalive heartbeat
    """
    await websocket_endpoint(websocket, session_id)


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    from pathlib import Path

    backend_dir = str(Path(__file__).resolve().parent.parent)
    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
        reload_dirs=[backend_dir],
        app_dir=backend_dir,
        log_level="info",
    )

# Made with Bob
