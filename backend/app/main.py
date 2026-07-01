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

# Import WebSocket handler
from app.api.websocket import websocket_endpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _warm_up_services():
    """Pre-load heavy services (embeddings model, ChromaDB) in a background thread.
    This prevents the first WebSocket connection from timing out waiting for them."""
    try:
        logger.info("⏳ Pre-loading RAG engine (embeddings + vector store)…")
        from app.api.websocket import get_rag_engine
        get_rag_engine()
        logger.info("✅ RAG engine ready")
    except Exception as exc:
        logger.error(f"⚠️  RAG engine warm-up failed: {exc}")


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("🚀 Starting Ephemeral Intent Synthesis System...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"API Host: {os.getenv('API_HOST', '0.0.0.0')}:{os.getenv('API_PORT', '8000')}")

    # Kick off heavy service initialisation in the background so the server
    # starts accepting connections immediately.  The first WS client that
    # arrives before warm-up finishes gets a friendly "not ready" message.
    t = threading.Thread(target=_warm_up_services, daemon=True)
    t.start()

    yield

    # Shutdown
    logger.info("🛑 Shutting down Ephemeral Intent Synthesis System...")


# Create FastAPI application
app = FastAPI(
    title="Ephemeral Intent Synthesis System",
    description="AI-powered biometric-adaptive educational interface system",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    lifespan=lifespan
)


# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    Returns system status and component health
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "components": {
            "api": "operational",
            "biometric_analyzer": "ready",
            "rag_engine": "ready",
            "ui_orchestrator": "ready"
        }
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with API information
    """
    return {
        "name": "Ephemeral Intent Synthesis System",
        "description": "AI-powered biometric-adaptive educational interface",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "biometric_analysis": "/api/v1/biometric/analyze",
            "knowledge_query": "/api/v1/knowledge/query",
            "ui_orchestration": "/api/v1/ui/orchestrate",
            "websocket": "/ws"
        }
    }


# System info endpoint
@app.get("/api/v1/system/info", tags=["System"])
async def system_info() -> Dict[str, Any]:
    """
    Get detailed system information
    """
    return {
        "system": {
            "name": "Ephemeral Intent Synthesis System",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "features": {
            "biometric_analysis": {
                "enabled": True,
                "description": "Real-time facial analysis and cognitive load detection"
            },
            "rag_engine": {
                "enabled": True,
                "mock_mode": os.getenv("MOCK_MODE", "false").lower() == "true",
                "description": "Knowledge retrieval and synthesis"
            },
            "ui_orchestration": {
                "enabled": True,
                "description": "Dynamic UI generation based on biometric context"
            },
            "lifecycle_management": {
                "enabled": True,
                "description": "Session monitoring and resource cleanup"
            }
        },
        "configuration": {
            "cors_enabled": True,
            "docs_enabled": os.getenv("ENABLE_DOCS", "true").lower() == "true",
            "metrics_enabled": os.getenv("ENABLE_METRICS", "true").lower() == "true"
        }
    }


# Biometric analysis endpoint (placeholder)
@app.post("/api/v1/biometric/analyze", tags=["Biometric"])
async def analyze_biometric(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze biometric data
    
    This endpoint will process facial landmarks and return cognitive load analysis
    """
    # TODO: Implement full biometric analysis
    return {
        "status": "success",
        "message": "Biometric analysis endpoint - implementation pending",
        "session_id": data.get("session_id", "unknown")
    }


# Knowledge query endpoint (placeholder)
@app.post("/api/v1/knowledge/query", tags=["Knowledge"])
async def query_knowledge(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query knowledge base and synthesize teaching modules
    
    This endpoint will use RAG to retrieve and synthesize educational content
    """
    # TODO: Implement full RAG query
    return {
        "status": "success",
        "message": "Knowledge query endpoint - implementation pending",
        "query": data.get("query", "unknown")
    }


# UI orchestration endpoint (placeholder)
@app.post("/api/v1/ui/orchestrate", tags=["UI"])
async def orchestrate_ui(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate dynamic UI configuration based on biometric context
    
    This endpoint will create adaptive UI components
    """
    # TODO: Implement full UI orchestration
    return {
        "status": "success",
        "message": "UI orchestration endpoint - implementation pending",
        "session_id": data.get("session_id", "unknown")
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_route(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time communication
    
    Connect to: ws://localhost:8000/ws/{session_id}
    
    Supported message types:
    - biometric_analysis: Analyze facial landmarks
    - knowledge_query: Query knowledge base
    - full_pipeline: Run complete analysis pipeline
    - ping: Health check
    """
    await websocket_endpoint(websocket, session_id)


# Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

# Made with Bob
