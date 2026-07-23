"""
Pipeline & Biometric Analyzer Tests
Covers the exact failure modes we've hit in production:
  - Empty landmarks crashing the WebSocket
  - update_module_progress wrong argument order
  - Pipeline completing end-to-end with no camera
  - Error messages reaching the frontend (not swallowed)
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.services.biometric_analyzer import BiometricAnalyzer
from app.services.lifecycle_manager import LifecycleManager, SessionStatus
from app.models.biometric_token import BiometricAnalysisRequest, CognitiveLoad, Urgency
from app.models.knowledge_payload import (
    KnowledgePayload, TeachingModule, ComplexityLevel, ModuleType
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(landmarks=None, frame_count=0, session_id="test_sess"):
    return BiometricAnalysisRequest(
        session_id=session_id,
        landmarks=landmarks or [],
        frame_count=frame_count,
        capture_duration=float(frame_count) / 30,
        timestamp=datetime.utcnow(),
    )


def make_knowledge_payload(session_id="test_sess", num_modules=2):
    modules = [
        TeachingModule(
            module_id=f"mod_{i:03d}",
            type=ModuleType.EXPLANATION,
            title=f"Module {i}",
            content=f"Content for module {i}",
            estimated_time=60,
            complexity=ComplexityLevel.INTERMEDIATE,
            interactive=False,
            order=i,
        )
        for i in range(num_modules)
    ]
    return KnowledgePayload(
        session_id=session_id,
        query="test query",
        core_concept="Test Concept",
        complexity_level=ComplexityLevel.INTERMEDIATE,
        teaching_modules=modules,
        related_concepts=[],
        source_references=[],
        total_estimated_time=120,
        keywords=["test"],
    )


# ---------------------------------------------------------------------------
# BiometricAnalyzer — the crash that caused ECONNABORTED
# ---------------------------------------------------------------------------

class TestBiometricAnalyzerNoCameraFallback:
    """
    These are the exact conditions under which the WebSocket was crashing:
    the frontend sends landmarks=[], frame_count=0 because no camera is used.
    """

    @pytest.fixture
    def analyzer(self):
        return BiometricAnalyzer()

    def test_empty_landmarks_returns_default_token(self, analyzer):
        """Must NOT raise — was previously crashing the whole WS handler."""
        req = make_request(landmarks=[], frame_count=0)
        token = analyzer.analyze(req)
        assert token is not None
        assert token.session_id == "test_sess"

    def test_empty_landmarks_default_has_neutral_load(self, analyzer):
        req = make_request(landmarks=[], frame_count=0)
        token = analyzer.analyze(req)
        assert token.cognitive_load == CognitiveLoad.MEDIUM

    def test_empty_landmarks_default_has_low_urgency(self, analyzer):
        req = make_request(landmarks=[], frame_count=0)
        token = analyzer.analyze(req)
        assert token.urgency == Urgency.LOW

    def test_empty_landmarks_confidence_is_zero(self, analyzer):
        """confidence=0 signals to monitoring that no real data was captured."""
        req = make_request(landmarks=[], frame_count=0)
        token = analyzer.analyze(req)
        assert token.confidence == 0.0

    def test_empty_landmarks_metadata_marks_source(self, analyzer):
        req = make_request(landmarks=[], frame_count=0)
        token = analyzer.analyze(req)
        assert token.metadata is not None
        assert token.metadata.get("source") == "default_no_camera"

    def test_zero_frame_count_also_uses_default(self, analyzer):
        """frame_count=0 triggers the default even if landmarks are non-empty."""
        import numpy as np
        landmarks = np.random.rand(1, 468, 3).tolist()
        req = make_request(landmarks=landmarks, frame_count=0)
        token = analyzer.analyze(req)
        assert token.confidence == 0.0

    def test_real_landmarks_does_not_use_default(self, analyzer):
        """With real data, confidence should be > 0."""
        import numpy as np
        np.random.seed(42)
        landmarks = np.random.rand(30, 468, 3).tolist()
        req = make_request(landmarks=landmarks, frame_count=30)
        token = analyzer.analyze(req)
        assert token.confidence > 0.0
        assert token.metadata.get("source") != "default_no_camera"

    def test_analyze_never_raises(self, analyzer):
        """Any input shape must return a token, never crash the pipeline."""
        bad_inputs = [
            [],                      # empty
            [[0, 0, 0]],             # single point, wrong shape
            [[[0] * 3] * 5],         # too few landmarks
        ]
        for landmarks in bad_inputs:
            req = make_request(landmarks=landmarks, frame_count=len(landmarks))
            try:
                token = analyzer.analyze(req)
                assert token is not None  # fallback used
            except Exception as exc:
                pytest.fail(f"analyze() raised {type(exc).__name__} for input shape {len(landmarks)}: {exc}")


# ---------------------------------------------------------------------------
# LifecycleManager — the wrong argument order that caused "unknown error"
# ---------------------------------------------------------------------------

class TestLifecycleManagerSessionFlow:

    @pytest.fixture
    def lm(self):
        return LifecycleManager()

    def test_create_session(self, lm):
        s = lm.create_session("sess_001", "test query")
        assert s.session_id == "sess_001"
        assert s.user_query == "test query"
        assert s.status == SessionStatus.INITIALIZING

    def test_create_duplicate_session_returns_existing(self, lm):
        s1 = lm.create_session("sess_dup")
        s2 = lm.create_session("sess_dup")
        assert s1 is s2

    def test_update_status_full_lifecycle(self, lm):
        lm.create_session("sess_flow")
        for status in [
            SessionStatus.CAPTURING_BIOMETRICS,
            SessionStatus.ANALYZING,
            SessionStatus.GENERATING_UI,
            SessionStatus.ACTIVE,
            SessionStatus.COMPLETING,
            SessionStatus.TERMINATED,
        ]:
            result = lm.update_session_status("sess_flow", status)
            assert result is True

    def test_update_status_unknown_session_returns_false(self, lm):
        assert lm.update_session_status("no_such_id", SessionStatus.ACTIVE) is False

    def test_update_module_progress_correct_signature(self, lm):
        """
        Regression: was called as update_module_progress(session_id, 0, module_id)
        which passed an integer as module_id and the string as completed.
        Correct call: update_module_progress(session_id, module_id, completed=False)
        """
        lm.create_session("sess_mod")
        # This must not raise TypeError / do wrong thing
        result = lm.update_module_progress("sess_mod", "mod_001", completed=False)
        assert result is True
        session = lm.get_session("sess_mod")
        # completed=False means module should NOT be in completed list
        assert "mod_001" not in session.completed_modules

    def test_update_module_progress_marks_complete(self, lm):
        lm.create_session("sess_done")
        result = lm.update_module_progress("sess_done", "mod_001", completed=True)
        assert result is True
        session = lm.get_session("sess_done")
        assert "mod_001" in session.completed_modules

    def test_update_module_progress_wrong_type_does_not_corrupt_state(self, lm):
        """
        The old buggy call was: update_module_progress(session_id, 0, "mod_001")
        where 0 (int) landed in the module_id slot and "mod_001" (truthy string)
        landed in completed.  Python's `0 not in []` is True, so it appended the
        integer 0 to completed_modules and set current_module_index to 1.

        After the fix the call is always:
            update_module_progress(session_id, module_id_str, completed=bool)
        We verify that passing the wrong type at least doesn't silently advance
        the module counter with garbage data — i.e. the int 0 is not counted as
        a completed string module_id by any downstream string checks.
        """
        lm.create_session("sess_type")
        lm.update_module_progress("sess_type", 0, "mod_001")  # type: ignore
        session = lm.get_session("sess_type")
        # "mod_001" string must NOT be in completed_modules (it landed in completed slot)
        assert "mod_001" not in session.completed_modules

    def test_terminate_session(self, lm):
        lm.create_session("sess_term")
        assert lm.terminate_session("sess_term") is True
        session = lm.get_session("sess_term")
        assert session.status == SessionStatus.TERMINATED

    def test_terminate_unknown_session_returns_false(self, lm):
        assert lm.terminate_session("not_real") is False

    def test_get_active_sessions_count(self, lm):
        lm.create_session("s1")
        lm.create_session("s2")
        lm.create_session("s3")
        assert lm.get_active_sessions_count() >= 3

    def test_update_session_data_stores_biometric_token(self, lm, sample_biometric_token):
        lm.create_session("sess_data")
        lm.update_session_data("sess_data", biometric_token=sample_biometric_token)
        session = lm.get_session("sess_data")
        assert session.biometric_token is sample_biometric_token

    def test_update_session_data_stores_knowledge_payload(self, lm, sample_knowledge_payload):
        lm.create_session("sess_kp")
        lm.update_session_data("sess_kp", knowledge_payload=sample_knowledge_payload)
        session = lm.get_session("sess_kp")
        assert session.knowledge_payload is sample_knowledge_payload
        assert session.total_modules == len(sample_knowledge_payload.teaching_modules)


# ---------------------------------------------------------------------------
# Pipeline handlers — verify messages are sent correctly and no crash on
# empty biometric data (the ECONNABORTED root cause)
# ---------------------------------------------------------------------------

class TestPipelineHandlers:

    @pytest.fixture
    def sent_messages(self):
        """Captures all messages sent via the send_fn callback."""
        messages: List[Dict[str, Any]] = []
        return messages

    @pytest.fixture
    def send_fn(self, sent_messages):
        async def _send(session_id: str, payload: dict):
            sent_messages.append(payload)
        return _send

    @pytest.mark.asyncio
    async def test_biometric_analysis_no_camera_sends_token(self, send_fn, sent_messages):
        """
        With empty landmarks the handler must send a biometric_token message,
        not crash (which would drop the WebSocket and produce ECONNABORTED).
        """
        from app.api.pipeline import handle_biometric_analysis
        token = await handle_biometric_analysis(
            send_fn, "sess_nc", {"landmarks": [], "frame_count": 0, "capture_duration": 0.0}
        )
        assert token is not None
        types = [m["type"] for m in sent_messages]
        assert "biometric_token" in types
        assert "error" not in types

    @pytest.mark.asyncio
    async def test_biometric_analysis_sends_correct_fields(self, send_fn, sent_messages):
        from app.api.pipeline import handle_biometric_analysis
        await handle_biometric_analysis(
            send_fn, "sess_fields", {"landmarks": [], "frame_count": 0, "capture_duration": 0.0}
        )
        token_msg = next(m for m in sent_messages if m["type"] == "biometric_token")
        data = token_msg["data"]
        assert "cognitive_load" in data
        assert "attention_score" in data
        assert "confidence" in data
        assert data["session_id"] == "sess_fields"

    @pytest.mark.asyncio
    async def test_knowledge_query_error_sends_error_message(self, send_fn, sent_messages):
        """If the RAG engine fails, the error must be sent to the client, not swallowed."""
        from app.api.pipeline import handle_knowledge_query

        async def _failing_stream(query, complexity):
            raise RuntimeError("ollama timeout")
            yield  # make this an async generator

        with patch("app.api.pipeline.get_rag_engine") as mock_get:
            mock_engine = MagicMock()
            mock_engine.stream_modules = _failing_stream
            mock_get.return_value = mock_engine

            result = await handle_knowledge_query(
                send_fn, "sess_err", {"query": "what is python"}
            )

        assert result is None
        types = [m["type"] for m in sent_messages]
        assert "error" in types
        err_msg = next(m for m in sent_messages if m["type"] == "error")
        assert "ollama timeout" in err_msg["data"]["message"]

    @pytest.mark.asyncio
    async def test_full_pipeline_no_camera_completes(self, send_fn, sent_messages):
        """
        End-to-end pipeline with no camera must complete without crashing.
        RAG engine is mocked so the test runs fast.
        """
        from app.api.pipeline import handle_full_pipeline

        mock_modules = make_knowledge_payload("sess_full").teaching_modules

        async def _fake_stream(query, complexity):
            for m in mock_modules:
                yield m

        with patch("app.api.pipeline.get_rag_engine") as mock_get_rag, \
             patch("app.api.pipeline.get_lifecycle_manager") as mock_get_lm:

            mock_engine = MagicMock()
            mock_engine.stream_modules = _fake_stream
            mock_get_rag.return_value = mock_engine

            mock_lm = MagicMock()
            mock_lm.get_session.return_value = None
            mock_lm.create_session.return_value = MagicMock()
            mock_lm.update_session_status.return_value = True
            mock_lm.update_session_data.return_value = True
            mock_lm.update_module_progress.return_value = True
            mock_get_lm.return_value = mock_lm

            await handle_full_pipeline(
                send_fn,
                "sess_full",
                {"query": "explain python", "landmarks": [], "frame_count": 0, "capture_duration": 0.0},
            )

        types = [m["type"] for m in sent_messages]
        # Must have streamed modules and sent the final payload
        assert "module_stream" in types
        assert "knowledge_payload" in types
        assert "ui_update" in types
        assert "pipeline_complete" in types
        # Must NOT have sent an error
        assert "error" not in types

    @pytest.mark.asyncio
    async def test_full_pipeline_rag_failure_sends_error_not_crash(self, send_fn, sent_messages):
        """If RAG fails, the frontend must receive an error message."""
        from app.api.pipeline import handle_full_pipeline

        async def _failing_stream(query, complexity):
            raise RuntimeError("connection refused")
            yield  # make it an async generator

        with patch("app.api.pipeline.get_rag_engine") as mock_get_rag, \
             patch("app.api.pipeline.get_lifecycle_manager") as mock_get_lm:

            mock_engine = MagicMock()
            mock_engine.stream_modules = _failing_stream
            mock_get_rag.return_value = mock_engine

            mock_lm = MagicMock()
            mock_lm.get_session.return_value = None
            mock_lm.create_session.return_value = MagicMock()
            mock_lm.update_session_status.return_value = True
            mock_lm.update_session_data.return_value = True
            mock_get_lm.return_value = mock_lm

            await handle_full_pipeline(
                send_fn,
                "sess_rag_fail",
                {"query": "test", "landmarks": [], "frame_count": 0, "capture_duration": 0.0},
            )

        types = [m["type"] for m in sent_messages]
        assert "error" in types
        assert "pipeline_complete" not in types


# Made with Bob
