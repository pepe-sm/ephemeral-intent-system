"""
WebSocket Endpoint for Real-Time Biometric Streaming
Handles real-time communication between frontend and backend services
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional
import json
import logging
import asyncio
from datetime import datetime

from app.services.biometric_analyzer import BiometricAnalyzer
from app.services.rag_engine import RAGEngine
from app.services.ui_orchestrator import UIOrchestrator
from app.models.biometric_token import BiometricAnalysisRequest
from app.models.knowledge_payload import RAGQueryRequest

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_data: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_data[session_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "message_count": 0
        }
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_data:
            del self.session_data[session_id]
        logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send a message to a specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)
            self.session_data[session_id]["message_count"] += 1
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {session_id}: {e}")


# Global connection manager
manager = ConnectionManager()

# Initialize services (lazy loading)
biometric_analyzer: Optional[BiometricAnalyzer] = None
rag_engine: Optional[RAGEngine] = None
ui_orchestrator: Optional[UIOrchestrator] = None


def get_biometric_analyzer() -> BiometricAnalyzer:
    """Get or create biometric analyzer instance"""
    global biometric_analyzer
    if biometric_analyzer is None:
        biometric_analyzer = BiometricAnalyzer()
        logger.info("BiometricAnalyzer initialized")
    return biometric_analyzer


def get_rag_engine() -> RAGEngine:
    """Get or create RAG engine instance"""
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
        logger.info("RAGEngine initialized")
    return rag_engine


def get_ui_orchestrator() -> UIOrchestrator:
    """Get or create UI orchestrator instance"""
    global ui_orchestrator
    if ui_orchestrator is None:
        ui_orchestrator = UIOrchestrator()
        logger.info("UIOrchestrator initialized")
    return ui_orchestrator


async def handle_biometric_analysis(session_id: str, data: Dict[str, Any]):
    """Handle biometric analysis request"""
    try:
        analyzer = get_biometric_analyzer()
        
        # Create analysis request
        request = BiometricAnalysisRequest(
            session_id=session_id,
            landmarks=data.get("landmarks", []),
            frame_count=data.get("frame_count", 0),
            capture_duration=data.get("capture_duration", 0.0),
            timestamp=datetime.utcnow()
        )
        
        # Analyze
        token = analyzer.analyze(request)
        
        # Send response with correct message type
        await manager.send_message(session_id, {
            "type": "biometric_token",
            "data": {
                "session_id": token.session_id,
                "cognitive_load": token.cognitive_load.value,
                "urgency": token.urgency.value,
                "attention_score": token.attention_score,
                "confidence": token.confidence,
                "stress_indicators": {
                    "blink_rate": token.stress_indicators.blink_rate,
                    "gaze_stability": token.stress_indicators.gaze_stability,
                    "micro_tension": token.stress_indicators.micro_tension,
                    "eye_aspect_ratio": token.stress_indicators.eye_aspect_ratio,
                    "head_pose_stability": token.stress_indicators.head_pose_stability
                },
                "timestamp": token.timestamp.isoformat()
            }
        })
        
        return token
        
    except Exception as e:
        logger.error(f"Error in biometric analysis: {e}", exc_info=True)
        await manager.send_message(session_id, {
            "type": "error",
            "error": "biometric_analysis_failed",
            "message": str(e)
        })
        return None


async def handle_knowledge_query(session_id: str, data: Dict[str, Any], biometric_token=None):
    """Handle knowledge query request"""
    try:
        engine = get_rag_engine()
        
        # Create query request
        request = RAGQueryRequest(
            session_id=session_id,
            query=data.get("query", ""),
            context=data.get("context"),
            max_sources=data.get("max_sources", 5),
            complexity_preference=data.get("complexity_preference")
        )
        
        logger.info(f"Querying RAG engine for: {request.query}")
        
        # Query knowledge base
        response = await engine.query(request)
        
        logger.info(f"RAG response received - success: {response.success}, modules: {len(response.knowledge_payload.teaching_modules)}")
        
        # Check if response is valid
        if not response.knowledge_payload or not response.knowledge_payload.teaching_modules:
            logger.error(f"RAG returned empty knowledge payload for session {session_id}")
            await manager.send_message(session_id, {
                "type": "error",
                "error": "empty_knowledge_payload",
                "message": "Knowledge base returned no content. Please try a different query or check if the knowledge base is populated."
            })
            return None
        
        # Send response with correct message type
        logger.info(f"Sending knowledge payload with {len(response.knowledge_payload.teaching_modules)} modules")
        await manager.send_message(session_id, {
            "type": "knowledge_payload",
            "data": {
                "session_id": response.session_id,
                "success": response.success,
                "core_concept": response.knowledge_payload.core_concept,
                "complexity_level": response.knowledge_payload.complexity_level.value,
                "teaching_modules": [
                    {
                        "module_id": m.module_id,
                        "type": m.type.value,
                        "title": m.title,
                        "content": m.content,
                        "estimated_time": m.estimated_time,
                        "order": m.order
                    }
                    for m in response.knowledge_payload.teaching_modules
                ],
                "total_estimated_time": response.knowledge_payload.total_estimated_time,
                "processing_time_ms": response.processing_time_ms
            }
        })
        
        logger.info(f"Knowledge payload sent successfully for session {session_id}")
        return response.knowledge_payload
        
    except Exception as e:
        logger.error(f"Error in knowledge query: {e}", exc_info=True)
        await manager.send_message(session_id, {
            "type": "error",
            "error": "knowledge_query_failed",
            "message": str(e)
        })
        return None


async def handle_ui_orchestration(session_id: str, biometric_token, knowledge_payload):
    """Handle UI orchestration request"""
    try:
        logger.info(f"UI orchestration handler called for session {session_id}")
        orchestrator = get_ui_orchestrator()
        logger.info(f"UI orchestrator obtained for session {session_id}")
        
        # Orchestrate UI
        logger.info(f"Calling orchestrator.orchestrate for session {session_id}")
        ui_config = orchestrator.orchestrate(biometric_token, knowledge_payload)
        logger.info(f"Orchestrator returned config for session {session_id}: {ui_config is not None}")
        
        # Restructure to match frontend expectations
        # Frontend expects: { root: {...}, presentation_config: {...} }
        component_tree_data = {
            "root": ui_config.get("component_tree", {}),
            "presentation_config": ui_config.get("presentation_config", {})
        }
        
        # Send response with correct message type and structure
        logger.info(f"Sending UI update message for session {session_id}")
        logger.info(f"Component tree data keys: {component_tree_data.keys()}")
        await manager.send_message(session_id, {
            "type": "ui_update",
            "data": {
                "component_tree": component_tree_data
            }
        })
        logger.info(f"UI update message sent successfully for session {session_id}")
        
        return ui_config
        
    except Exception as e:
        logger.error(f"Error in UI orchestration: {e}", exc_info=True)
        await manager.send_message(session_id, {
            "type": "error",
            "error": "ui_orchestration_failed",
            "message": str(e)
        })
        return None


async def handle_full_pipeline(session_id: str, data: Dict[str, Any]):
    """Handle full pipeline: biometric -> knowledge -> UI"""
    try:
        # Step 1: Biometric Analysis
        await manager.send_message(session_id, {
            "type": "pipeline_status",
            "step": "biometric_analysis",
            "status": "processing"
        })
        
        # Extract biometric data from flat structure
        biometric_data = {
            "landmarks": data.get("landmarks", []),
            "frame_count": data.get("frame_count", 0),
            "capture_duration": data.get("capture_duration", 0.0)
        }
        
        biometric_token = await handle_biometric_analysis(session_id, biometric_data)
        if not biometric_token:
            return
        
        # Step 2: Knowledge Query
        await manager.send_message(session_id, {
            "type": "pipeline_status",
            "step": "knowledge_query",
            "status": "processing"
        })
        
        # Extract query data from flat structure
        query_data = {
            "query": data.get("query", ""),
            "session_id": session_id
        }
        
        knowledge_payload = await handle_knowledge_query(
            session_id,
            query_data,
            biometric_token
        )
        if not knowledge_payload:
            # Send error message to frontend
            await manager.send_message(session_id, {
                "type": "error",
                "error": "knowledge_query_failed",
                "message": "Failed to generate knowledge payload. The knowledge base may be empty or the query failed."
            })
            logger.error(f"Knowledge query returned None for session {session_id}")
            return
        
        # Step 3: UI Orchestration
        logger.info(f"Starting UI orchestration for session {session_id}")
        await manager.send_message(session_id, {
            "type": "pipeline_status",
            "step": "ui_orchestration",
            "status": "processing"
        })
        
        ui_config = await handle_ui_orchestration(session_id, biometric_token, knowledge_payload)
        logger.info(f"UI orchestration completed for session {session_id}, config: {ui_config is not None}")
        if not ui_config:
            # Send error message to frontend
            await manager.send_message(session_id, {
                "type": "error",
                "error": "ui_orchestration_failed",
                "message": "Failed to generate UI configuration."
            })
            logger.error(f"UI orchestration returned None for session {session_id}")
            return
        
        # Pipeline complete
        await manager.send_message(session_id, {
            "type": "pipeline_complete",
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error in full pipeline: {e}", exc_info=True)
        await manager.send_message(session_id, {
            "type": "error",
            "error": "pipeline_failed",
            "message": str(e)
        })


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Main WebSocket endpoint handler
    
    Handles real-time communication for:
    - Biometric data streaming
    - Knowledge queries
    - UI orchestration
    - Full pipeline execution
    """
    await manager.connect(websocket, session_id)
    
    try:
        # Send welcome message
        await manager.send_message(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "WebSocket connection established"
        })
        
        # Message loop
        while True:
            # Receive message
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            logger.info(f"Received message type: {message_type} from {session_id}")
            
            # Route message to appropriate handler
            if message_type == "biometric_analysis":
                await handle_biometric_analysis(session_id, data.get("data", {}))
            
            elif message_type == "knowledge_query":
                await handle_knowledge_query(session_id, data.get("data", {}))
            
            elif message_type == "full_pipeline":
                await handle_full_pipeline(session_id, data.get("data", {}))
            
            elif message_type == "ping":
                await manager.send_message(session_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            else:
                await manager.send_message(session_id, {
                    "type": "error",
                    "error": "unknown_message_type",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Client disconnected: {session_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}", exc_info=True)
        manager.disconnect(session_id)


# Made with Bob for IBM AI Builders Challenge