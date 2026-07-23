"""
WebSocket Endpoint
Handles connection management and message routing only.
All pipeline logic lives in app.api.pipeline.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any
import logging
from datetime import datetime

from app.api.pipeline import (
    handle_biometric_analysis,
    handle_knowledge_query,
    handle_full_pipeline,
    is_rag_ready,
    get_rag_engine,  # re-exported so main.py warm-up import still works
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Tracks open WebSocket connections keyed by session_id."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._message_counts: Dict[str, int] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self._message_counts[session_id] = 0
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str) -> None:
        self.active_connections.pop(session_id, None)
        self._message_counts.pop(session_id, None)
        logger.info(f"WebSocket disconnected: {session_id}")

    async def send(self, session_id: str, message: Dict[str, Any]) -> None:
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_json(message)
            self._message_counts[session_id] = self._message_counts.get(session_id, 0) + 1

    async def broadcast(self, message: Dict[str, Any]) -> None:
        for sid, ws in list(self.active_connections.items()):
            try:
                await ws.send_json(message)
            except Exception as exc:
                logger.error(f"Broadcast error to {sid}: {exc}")


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------

async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket entry point.  Accepts the connection, routes messages to
    pipeline handlers, and cleans up on disconnect.

    Message types handled:
      full_pipeline       — biometric + knowledge + UI in one shot
      biometric_analysis  — biometric step only
      knowledge_query     — knowledge step only
      ping                — keepalive
    """
    await manager.connect(websocket, session_id)

    # Convenience closure so pipeline handlers can call manager.send
    async def send(sid: str, payload: Dict[str, Any]) -> None:
        await manager.send(sid, payload)

    try:
        # Warn if the RAG engine is still warming up
        if not is_rag_ready():
            await send(session_id, {
                "type": "pipeline_status",
                "data": {
                    "step": "startup",
                    "status": "warming_up",
                    "message": "Server is loading AI models — please wait a moment, then try again.",
                },
            })

        await send(session_id, {
            "type": "connection_established",
            "data": {
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "WebSocket connection established",
            },
        })

        # Message loop
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            logger.info(f"Message [{msg_type}] from {session_id}")

            if msg_type == "full_pipeline":
                await handle_full_pipeline(send, session_id, data.get("data", {}))

            elif msg_type == "biometric_analysis":
                await handle_biometric_analysis(send, session_id, data.get("data", {}))

            elif msg_type == "knowledge_query":
                await handle_knowledge_query(send, session_id, data.get("data", {}))

            elif msg_type == "ping":
                await send(session_id, {
                    "type": "pong",
                    "data": {"timestamp": datetime.utcnow().isoformat()},
                })

            else:
                await send(session_id, {
                    "type": "error",
                    "data": {
                        "error": "unknown_message_type",
                        "message": f"Unknown message type: {msg_type}",
                    },
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)

    except Exception as exc:
        logger.error(f"WebSocket error [{session_id}]: {exc}", exc_info=True)
        manager.disconnect(session_id)


# Made with Bob
