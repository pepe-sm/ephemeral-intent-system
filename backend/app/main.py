"""
FastAPI Main Application Entry Point
Ephemeral Intent Synthesis System
"""

# Load .env before anything else so every os.getenv() call sees the values.
# override=True ensures .env always wins even if variables were already set
# in the shell environment from a previous (broken) run.
from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, WebSocket, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import os

from app.api.websocket import websocket_endpoint
from app.api.pipeline import get_rag_engine, is_rag_ready, get_lifecycle_manager, get_session_videos
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


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Silence browser favicon requests — return 204 No Content."""
    from fastapi.responses import Response
    return Response(status_code=204)


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
# Resource ingestion endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/resources/ingest", tags=["Resources"])
async def ingest_resource(
    title: str = Form(...),
    source_url: str = Form(""),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
) -> Dict[str, Any]:
    """
    Add a resource to the RAG knowledge base.

    Accepts either:
      - A plain-text/markdown body via the ``text`` form field.
      - A file upload (.txt, .md, .pdf) via the ``file`` field.

    Both can be sent together; if both are present both are ingested under
    the same ``source_id``.
    """
    if not text and not file:
        raise HTTPException(status_code=422, detail="Provide 'text' or a file upload.")

    from langchain_core.documents import Document as LCDocument

    source_id = str(uuid.uuid4())
    base_meta = {
        "source_id": source_id,
        "title": title,
        "source_url": source_url or None,
        "ingested_at": datetime.utcnow().isoformat(),
    }

    docs: list = []

    # -- plain text / markdown --
    if text and text.strip():
        docs.append(LCDocument(
            page_content=text.strip(),
            metadata={**base_meta, "content_type": "text"},
        ))

    # -- file upload --
    if file:
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext in ("txt", "md", ""):
            raw = await file.read()
            content = raw.decode("utf-8", errors="replace").strip()
            if content:
                docs.append(LCDocument(
                    page_content=content,
                    metadata={**base_meta, "content_type": ext or "text", "filename": filename},
                ))

        elif ext == "pdf":
            try:
                import pypdf  # type: ignore
                import io
                raw = await file.read()
                reader = pypdf.PdfReader(io.BytesIO(raw))
                pages = []
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        pages.append(LCDocument(
                            page_content=page_text.strip(),
                            metadata={**base_meta, "content_type": "pdf",
                                      "filename": filename, "page": i + 1},
                        ))
                docs.extend(pages)
            except ImportError:
                raise HTTPException(
                    status_code=422,
                    detail="PDF support requires pypdf. Install it: pip install pypdf",
                )
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type '.{ext}'. Use .txt, .md, or .pdf.",
            )

    if not docs:
        raise HTTPException(status_code=422, detail="No extractable content found.")

    engine = get_rag_engine()
    chunk_count = engine.add_documents(docs)

    return {
        "source_id": source_id,
        "title": title,
        "chunks_added": chunk_count,
        "documents_processed": len(docs),
    }


@app.get("/api/v1/resources", tags=["Resources"])
async def list_resources() -> Dict[str, Any]:
    """Return all resources currently indexed in the vector store."""
    engine = get_rag_engine()
    resources = engine.list_resources()
    return {"resources": resources, "count": len(resources)}


@app.delete("/api/v1/resources/{source_id}", tags=["Resources"])
async def delete_resource(source_id: str) -> Dict[str, Any]:
    """Remove all chunks for a given source_id from the vector store."""
    engine = get_rag_engine()
    deleted = engine.delete_resource(source_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Resource not found.")
    return {"deleted": True, "source_id": source_id, "chunks_removed": deleted}


@app.post("/api/v1/resources/ingest-url", tags=["Resources"])
async def ingest_resource_url(
    title: str = Form(...),
    url: str = Form(...),
) -> Dict[str, Any]:
    """
    Fetch a web page by URL and add its text content to the RAG knowledge base.
    Uses httpx for the HTTP request and stdlib html.parser for extraction.
    """
    import re
    from html.parser import HTMLParser
    import httpx
    from langchain_core.documents import Document as LCDocument

    class _TextExtractor(HTMLParser):
        """Strip all HTML tags; skip <script> and <style> blocks."""
        def __init__(self):
            super().__init__()
            self.parts: list = []
            self._skip = False

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "noscript"):
                self._skip = True

        def handle_endtag(self, tag):
            if tag in ("script", "style", "noscript"):
                self._skip = False

        def handle_data(self, data):
            if not self._skip:
                self.parts.append(data)

        def get_text(self) -> str:
            raw = " ".join(self.parts)
            # collapse whitespace
            return re.sub(r"\s{2,}", " ", raw).strip()

    # Fetch the page
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; EphemeralBot/1.0)"})
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=422, detail=f"HTTP {exc.response.status_code} fetching URL.")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not fetch URL: {exc}")

    # Extract text
    parser = _TextExtractor()
    parser.feed(resp.text)
    text = parser.get_text()

    if len(text) < 50:
        raise HTTPException(status_code=422, detail="Page returned too little text to be useful.")

    source_id = str(uuid.uuid4())
    doc = LCDocument(
        page_content=text[:50_000],   # cap at 50 K chars to avoid huge embeddings
        metadata={
            "source_id": source_id,
            "title": title,
            "source_url": url,
            "content_type": "url",
            "ingested_at": datetime.utcnow().isoformat(),
        },
    )

    engine = get_rag_engine()
    chunk_count = engine.add_documents([doc])

    return {
        "source_id": source_id,
        "title": title,
        "chunks_added": chunk_count,
        "documents_processed": 1,
        "characters_extracted": len(text),
    }


# ---------------------------------------------------------------------------
# Video registry polling
# ---------------------------------------------------------------------------

@app.get("/api/v1/sessions/{session_id}/videos", tags=["Video"])
async def get_session_video_registry(session_id: str) -> Dict[str, Any]:
    """
    Poll for all videos generated for a session.
    Returns {module_id: video_url} map.

    The frontend calls this after reconnecting or on page load to pick up
    any videos that were generated while the WebSocket was closed.
    """
    videos = get_session_videos(session_id)
    return {"session_id": session_id, "videos": videos, "count": len(videos)}


# ---------------------------------------------------------------------------
# Video file serving
# ---------------------------------------------------------------------------

@app.get("/api/v1/video/{filename}", tags=["Video"])
async def serve_video(filename: str) -> FileResponse:
    """Serve a generated MP4 file from the video output directory."""
    from pathlib import Path
    video_dir = Path(os.getenv("VIDEO_OUTPUT_DIR", "./data/videos"))
    # Sanitise — prevent path traversal
    safe_name = Path(filename).name
    video_path = video_dir / safe_name
    if not video_path.exists() or video_path.suffix.lower() != ".mp4":
        raise HTTPException(status_code=404, detail="Video not found.")
    return FileResponse(str(video_path), media_type="video/mp4")


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
