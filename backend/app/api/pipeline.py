"""
Pipeline Handlers
Extracted from websocket.py — all full-pipeline, individual-step, and
orchestration logic lives here.  websocket.py handles only the WS connection
and message routing.
"""

from typing import Dict, Any, Optional, List
import asyncio
import logging
import os
import threading
from datetime import datetime

from app.services.biometric_analyzer import BiometricAnalyzer
from app.services.rag_engine import RAGEngine
from app.services.ui_orchestrator import UIOrchestrator
from app.services.lifecycle_manager import LifecycleManager, SessionStatus
from app.services.video_generator import VideoGenerator
from app.models.biometric_token import BiometricAnalysisRequest, BiometricToken
from app.models.knowledge_payload import RAGQueryRequest, KnowledgePayload

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory video registry
# session_id → {module_id → video_url}
# Persists even after the WebSocket closes so the frontend can poll for videos.
# ---------------------------------------------------------------------------
_video_registry: Dict[str, Dict[str, str]] = {}
_video_registry_lock = threading.Lock()


def register_video(session_id: str, module_id: str, video_url: str) -> None:
    with _video_registry_lock:
        if session_id not in _video_registry:
            _video_registry[session_id] = {}
        _video_registry[session_id][module_id] = video_url


def get_session_videos(session_id: str) -> Dict[str, str]:
    """Return {module_id: video_url} for a session."""
    with _video_registry_lock:
        return dict(_video_registry.get(session_id, {}))

# ---------------------------------------------------------------------------
# Service singletons — initialised lazily, one instance for the process life
# ---------------------------------------------------------------------------

_biometric_analyzer: Optional[BiometricAnalyzer] = None
_rag_engine: Optional[RAGEngine] = None
_ui_orchestrator: Optional[UIOrchestrator] = None
_lifecycle_manager: Optional[LifecycleManager] = None
_video_generator: Optional[VideoGenerator] = None
_rag_lock = threading.Lock()  # Prevent double-init on first request


def get_biometric_analyzer() -> BiometricAnalyzer:
    global _biometric_analyzer
    if _biometric_analyzer is None:
        _biometric_analyzer = BiometricAnalyzer()
        logger.info("BiometricAnalyzer initialised")
    return _biometric_analyzer


def get_rag_engine() -> RAGEngine:
    """First call blocks (~30 s on cold start) while embeddings load.
    main.py kicks this off in a background thread at startup.
    Lock prevents two concurrent callers both entering the init path."""
    global _rag_engine
    if _rag_engine is not None:
        return _rag_engine
    with _rag_lock:
        # Re-check inside lock — warm-up thread may have finished while we waited
        if _rag_engine is None:
            _rag_engine = RAGEngine()
            logger.info("RAGEngine initialised")
    return _rag_engine


def is_rag_ready() -> bool:
    return _rag_engine is not None


def get_ui_orchestrator() -> UIOrchestrator:
    global _ui_orchestrator
    if _ui_orchestrator is None:
        _ui_orchestrator = UIOrchestrator()
        logger.info("UIOrchestrator initialised")
    return _ui_orchestrator


def get_lifecycle_manager() -> LifecycleManager:
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager()
        logger.info("LifecycleManager initialised")
    return _lifecycle_manager


def get_video_generator() -> VideoGenerator:
    global _video_generator
    if _video_generator is None:
        _video_generator = VideoGenerator()
        logger.info("VideoGenerator initialised (pipeline)")
    return _video_generator


# ---------------------------------------------------------------------------
# Typed send helper (injected by websocket.py)
# ---------------------------------------------------------------------------

async def _send(send_fn, session_id: str, payload: Dict[str, Any]) -> None:
    """Thin wrapper so handlers don't need a reference to ConnectionManager."""
    await send_fn(session_id, payload)


# ---------------------------------------------------------------------------
# Individual step handlers
# ---------------------------------------------------------------------------

async def handle_biometric_analysis(
    send_fn,
    session_id: str,
    data: Dict[str, Any],
) -> Optional[BiometricToken]:
    try:
        analyzer = get_biometric_analyzer()
        request = BiometricAnalysisRequest(
            session_id=session_id,
            landmarks=data.get("landmarks", []),
            frame_count=data.get("frame_count", 0),
            capture_duration=data.get("capture_duration", 0.0),
            timestamp=datetime.utcnow(),
        )
        token = analyzer.analyze(request)

        await _send(send_fn, session_id, {
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
                    "head_pose_stability": token.stress_indicators.head_pose_stability,
                },
                "timestamp": token.timestamp.isoformat(),
            },
        })
        return token

    except Exception as exc:
        logger.error(f"Biometric analysis error [{session_id}]: {exc}", exc_info=True)
        err_msg = str(exc) or f"Biometric analysis error: {type(exc).__name__}"
        await _send(send_fn, session_id, {
            "type": "error",
            "data": {"error": "biometric_analysis_failed", "message": err_msg},
        })
        return None


async def _safe_send(send_fn, session_id: str, payload: Dict[str, Any]) -> bool:
    """Send a WS message, silently returning False if the socket has closed."""
    try:
        await send_fn(session_id, payload)
        return True
    except Exception:
        return False


async def _run_video_pipeline(
    send_fn,
    session_id: str,
    modules: list,
    voice_pace: str,
    vg: VideoGenerator,
) -> None:
    """
    Background task: generate one video per module SEQUENTIALLY after all
    content has been streamed.

    Sequential execution is intentional:
      - Wav2Lip is CPU-heavy; parallel runs overload the machine.
      - The user already has all text; video is an enhancement.

    Each finished video is:
      1. Registered in the in-process video registry (survives WS close).
      2. Pushed via WS if the socket is still open.

    The frontend polls /api/v1/sessions/{session_id}/videos to pick up
    any videos it missed while the WS was reconnecting.
    """
    logger.info(f"[VideoJob] Starting sequential video generation for {len(modules)} modules [{session_id}]")
    for module in modules:
        module_id = module.module_id
        # Cap script to first 2 sentences from the content body (~20-30 words).
        # Full paragraphs = 200+ words → 60-70s audio → 5-7 min Wav2Lip on CPU.
        # First 2 sentences of content keeps audio ~10s → ~50s Wav2Lip on CPU.
        import re as _re
        content_sentences = _re.split(r'(?<=[.!?])\s+', module.content.strip())
        body = " ".join(content_sentences[:2]).strip()
        script = f"{module.title}. {body}" if body else module.title
        logger.info(f"[VideoJob] Script for {module_id}: {len(script.split())} words — '{script[:80]}…'")
        try:
            result = await vg.generate_async(
                script=script,
                session_id=session_id,
                voice_pace=voice_pace,
            )
            if result.success and result.video_path and not result.is_mock:
                video_url = f"/api/v1/video/{result.video_path.name}"
                # Always register — survives WS close
                register_video(session_id, module_id, video_url)
                # Push WS notification (best-effort)
                delivered = await _safe_send(send_fn, session_id, {
                    "type": "video_ready",
                    "data": {
                        "module_id": module_id,
                        "video_url": video_url,
                        "generation_time_ms": result.generation_time_ms,
                    },
                })
                logger.info(
                    f"[VideoJob] {module_id} ready in {result.generation_time_ms:.0f}ms "
                    f"(WS {'delivered' if delivered else 'closed — stored in registry'}) [{session_id}]"
                )
            elif result.is_mock:
                logger.debug(f"[VideoJob] Mock result for {module_id} — pipeline not configured")
            else:
                logger.warning(f"[VideoJob] Generation failed for {module_id}: {result.error}")
        except Exception as exc:
            logger.warning(f"[VideoJob] Exception for {module_id} [{session_id}]: {exc}", exc_info=True)

    logger.info(f"[VideoJob] All videos complete for session {session_id}")


async def handle_knowledge_query(
    send_fn,
    session_id: str,
    data: Dict[str, Any],
    biometric_token: Optional[BiometricToken] = None,
) -> Optional[KnowledgePayload]:
    """
    Phase 1 — Stream content: yield TeachingModule objects to the frontend
    one at a time as the LLM generates them (fast first-byte).

    Phase 2 — Generate videos: after ALL modules are collected, fire a
    single background task that produces one MP4 per module sequentially.
    Videos are pushed via WS and also stored in the video registry so the
    frontend can poll for them even if the WS has closed.
    """
    from app.models.knowledge_payload import ComplexityLevel, KnowledgePayload
    from datetime import datetime

    try:
        engine = get_rag_engine()
        query = data.get("query", "")
        complexity = data.get("complexity_preference") or ComplexityLevel.INTERMEDIATE
        voice_pace = data.get("voice_pace", "normal")
        logger.info(f"RAG query (streaming) [{session_id}]: {query}")

        collected: list = []

        # ── Phase 1: stream modules ────────────────────────────────────────
        async for module in engine.stream_modules(query, complexity):
            collected.append(module)
            await _send(send_fn, session_id, {
                "type": "module_stream",
                "data": {
                    "session_id": session_id,
                    "module": {
                        "module_id": module.module_id,
                        "type": module.type.value,
                        "title": module.title,
                        "content": module.content,
                        "estimated_time": module.estimated_time,
                        "order": module.order,
                    },
                    "index": len(collected) - 1,
                    "is_first": len(collected) == 1,
                },
            })
            logger.info(f"Module {module.module_id} streamed [{session_id}]: {module.title[:40]}")

        if not collected:
            await _send(send_fn, session_id, {
                "type": "error",
                "data": {
                    "error": "empty_knowledge_payload",
                    "message": "The AI returned no content. Please try a different query.",
                },
            })
            return None

        # Build and send the final consolidated payload
        core_concept = " ".join(query.split()[:5]).title()
        total_time = sum(m.estimated_time for m in collected)

        payload = KnowledgePayload(
            session_id=session_id,
            query=query,
            core_concept=core_concept,
            complexity_level=complexity,
            teaching_modules=collected,
            related_concepts=[],
            source_references=[],
            total_estimated_time=total_time,
            keywords=query.lower().split()[:5],
            timestamp=datetime.utcnow().isoformat(),
        )

        await _send(send_fn, session_id, {
            "type": "knowledge_payload",
            "data": {
                "session_id": session_id,
                "success": True,
                "core_concept": payload.core_concept,
                "complexity_level": payload.complexity_level.value,
                "teaching_modules": [
                    {
                        "module_id": m.module_id,
                        "type": m.type.value,
                        "title": m.title,
                        "content": m.content,
                        "estimated_time": m.estimated_time,
                        "order": m.order,
                    }
                    for m in collected
                ],
                "total_estimated_time": total_time,
                "processing_time_ms": 0,
            },
        })
        logger.info(f"Knowledge payload sent [{session_id}] — {len(collected)} modules")

        # ── Phase 2: kick off video generation AFTER all content is ready ─
        vg = get_video_generator()
        if vg.is_ready():
            # Fire-and-forget background task — sequential, one MP4 per module
            asyncio.ensure_future(
                _run_video_pipeline(send_fn, session_id, list(collected), voice_pace, vg)
            )
            logger.info(f"Video pipeline scheduled for {len(collected)} modules [{session_id}]")

        return payload

    except Exception as exc:
        logger.error(f"Knowledge query error [{session_id}]: {exc}", exc_info=True)
        err_msg = str(exc) or f"Knowledge query error: {type(exc).__name__}"
        await _send(send_fn, session_id, {
            "type": "error",
            "data": {"error": "knowledge_query_failed", "message": err_msg},
        })
        return None


async def handle_ui_orchestration(
    send_fn,
    session_id: str,
    biometric_token: BiometricToken,
    knowledge_payload: KnowledgePayload,
) -> Optional[Dict[str, Any]]:
    try:
        orchestrator = get_ui_orchestrator()
        ui_config = orchestrator.orchestrate(biometric_token, knowledge_payload)

        component_tree_data = {
            "root": ui_config.get("component_tree", {}),
            "presentation_config": ui_config.get("presentation_config", {}),
        }

        await _send(send_fn, session_id, {
            "type": "ui_update",
            "data": {"component_tree": component_tree_data},
        })
        logger.info(f"UI update sent [{session_id}]")
        return ui_config

    except Exception as exc:
        logger.error(f"UI orchestration error [{session_id}]: {exc}", exc_info=True)
        err_msg = str(exc) or f"UI orchestration error: {type(exc).__name__}"
        await _send(send_fn, session_id, {
            "type": "error",
            "data": {"error": "ui_orchestration_failed", "message": err_msg},
        })
        return None


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

async def handle_full_pipeline(send_fn, session_id: str, data: Dict[str, Any]) -> None:
    lm = get_lifecycle_manager()

    # Register session with lifecycle manager
    if not lm.get_session(session_id):
        lm.create_session(session_id, user_query=data.get("query", ""))

    try:
        # ── Step 1: Biometric analysis ─────────────────────────────────────
        lm.update_session_status(session_id, SessionStatus.CAPTURING_BIOMETRICS)
        await _send(send_fn, session_id, {
            "type": "pipeline_status",
            "data": {"step": "biometric_analysis", "status": "processing"},
        })

        biometric_token = await handle_biometric_analysis(
            send_fn,
            session_id,
            {
                "landmarks": data.get("landmarks", []),
                "frame_count": data.get("frame_count", 0),
                "capture_duration": data.get("capture_duration", 0.0),
            },
        )
        if not biometric_token:
            lm.update_session_status(session_id, SessionStatus.ERROR)
            return

        lm.update_session_data(session_id, biometric_token=biometric_token)
        lm.update_session_status(session_id, SessionStatus.ANALYZING)

        # ── Step 2: Knowledge query ────────────────────────────────────────
        await _send(send_fn, session_id, {
            "type": "pipeline_status",
            "data": {"step": "knowledge_query", "status": "processing"},
        })

        knowledge_payload = await handle_knowledge_query(
            send_fn,
            session_id,
            {"query": data.get("query", ""), "session_id": session_id},
            biometric_token,
        )
        if not knowledge_payload:
            lm.update_session_status(session_id, SessionStatus.ERROR)
            return

        lm.update_session_data(session_id, knowledge_payload=knowledge_payload)
        lm.update_session_status(session_id, SessionStatus.GENERATING_UI)

        # ── Step 3: UI orchestration ───────────────────────────────────────
        await _send(send_fn, session_id, {
            "type": "pipeline_status",
            "data": {"step": "ui_orchestration", "status": "processing"},
        })

        ui_config = await handle_ui_orchestration(
            send_fn, session_id, biometric_token, knowledge_payload
        )
        if not ui_config:
            lm.update_session_status(session_id, SessionStatus.ERROR)
            return

        lm.update_session_data(session_id, ui_config=ui_config)
        lm.update_session_status(session_id, SessionStatus.ACTIVE)
        # update_module_progress(session_id, module_id, completed)
        # — pass the first module's ID, not an index
        if knowledge_payload.teaching_modules:
            first_module_id = knowledge_payload.teaching_modules[0].module_id
            lm.update_module_progress(session_id, first_module_id, completed=False)

        # ── Complete ───────────────────────────────────────────────────────
        await _send(send_fn, session_id, {
            "type": "pipeline_complete",
            "data": {"status": "success"},
        })

    except Exception as exc:
        logger.error(f"Full pipeline error [{session_id}]: {exc}", exc_info=True)
        lm.update_session_status(session_id, SessionStatus.ERROR)
        err_msg = str(exc) or f"Pipeline error: {type(exc).__name__}"
        await _send(send_fn, session_id, {
            "type": "error",
            "data": {"error": "pipeline_failed", "message": err_msg},
        })


# Made with Bob
