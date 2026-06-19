"""
Unit Tests for Data Models
Tests BiometricToken and KnowledgePayload models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.biometric_token import (
    BiometricToken,
    BiometricUpdate,
    BiometricAnalysisRequest,
    CognitiveLoad,
    Urgency,
    StressIndicators,
    EmotionScores
)

from app.models.knowledge_payload import (
    KnowledgePayload,
    TeachingModule,
    SourceReference,
    RAGQueryRequest,
    RAGQueryResponse,
    ComplexityLevel,
    ModuleType
)


class TestStressIndicators:
    """Test StressIndicators model"""
    
    def test_valid_stress_indicators(self):
        """Test creating valid stress indicators"""
        indicators = StressIndicators(
            blink_rate=15.5,
            gaze_stability=0.85,
            micro_tension=0.45,
            eye_aspect_ratio=0.28,
            head_pose_stability=0.82
        )
        
        assert indicators.blink_rate == 15.5
        assert indicators.gaze_stability == 0.85
        assert indicators.micro_tension == 0.45
        assert indicators.eye_aspect_ratio == 0.28
        assert indicators.head_pose_stability == 0.82
    
    def test_stress_indicators_validation(self):
        """Test validation of stress indicators"""
        # Test blink_rate out of range
        with pytest.raises(ValidationError):
            StressIndicators(
                blink_rate=150,  # Too high
                gaze_stability=0.85,
                micro_tension=0.45,
                eye_aspect_ratio=0.28
            )
        
        # Test gaze_stability out of range
        with pytest.raises(ValidationError):
            StressIndicators(
                blink_rate=15.5,
                gaze_stability=1.5,  # Too high
                micro_tension=0.45,
                eye_aspect_ratio=0.28
            )


class TestEmotionScores:
    """Test EmotionScores model"""
    
    def test_valid_emotion_scores(self):
        """Test creating valid emotion scores"""
        emotions = EmotionScores(
            neutral=0.6,
            happy=0.2,
            sad=0.05,
            angry=0.05,
            fearful=0.05,
            disgusted=0.03,
            surprised=0.02
        )
        
        assert emotions.neutral == 0.6
        assert emotions.happy == 0.2
        assert sum([
            emotions.neutral, emotions.happy, emotions.sad,
            emotions.angry, emotions.fearful, emotions.disgusted,
            emotions.surprised
        ]) == pytest.approx(1.0)
    
    def test_emotion_scores_defaults(self):
        """Test default emotion scores"""
        emotions = EmotionScores()
        
        assert emotions.neutral == 0.0
        assert emotions.happy == 0.0
        assert emotions.sad == 0.0


class TestBiometricToken:
    """Test BiometricToken model"""
    
    def test_valid_biometric_token(self):
        """Test creating a valid biometric token"""
        stress_indicators = StressIndicators(
            blink_rate=18.5,
            gaze_stability=0.72,
            micro_tension=0.64,
            eye_aspect_ratio=0.25,
            head_pose_stability=0.78
        )
        
        token = BiometricToken(
            session_id="sess_test123",
            cognitive_load=CognitiveLoad.HIGH,
            urgency=Urgency.IMMEDIATE,
            attention_score=0.85,
            stress_indicators=stress_indicators,
            confidence=0.92
        )
        
        assert token.session_id == "sess_test123"
        assert token.cognitive_load == CognitiveLoad.HIGH
        assert token.urgency == Urgency.IMMEDIATE
        assert token.attention_score == 0.85
        assert token.confidence == 0.92
        assert isinstance(token.timestamp, datetime)
    
    def test_biometric_token_with_emotions(self):
        """Test biometric token with emotion scores"""
        stress_indicators = StressIndicators(
            blink_rate=15.0,
            gaze_stability=0.8,
            micro_tension=0.5,
            eye_aspect_ratio=0.3
        )
        
        emotions = EmotionScores(
            neutral=0.5,
            happy=0.3,
            sad=0.1,
            angry=0.05,
            fearful=0.03,
            disgusted=0.01,
            surprised=0.01
        )
        
        token = BiometricToken(
            session_id="sess_test456",
            cognitive_load=CognitiveLoad.MEDIUM,
            urgency=Urgency.MODERATE,
            attention_score=0.75,
            stress_indicators=stress_indicators,
            emotion_scores=emotions,
            confidence=0.88
        )
        
        assert token.emotion_scores is not None
        assert token.emotion_scores.neutral == 0.5
        assert token.emotion_scores.happy == 0.3
    
    def test_biometric_token_with_metadata(self):
        """Test biometric token with metadata"""
        stress_indicators = StressIndicators(
            blink_rate=15.0,
            gaze_stability=0.8,
            micro_tension=0.5,
            eye_aspect_ratio=0.3
        )
        
        metadata = {
            "frames_processed": 90,
            "processing_time_ms": 245,
            "landmarks_detected": 468
        }
        
        token = BiometricToken(
            session_id="sess_test789",
            cognitive_load=CognitiveLoad.LOW,
            urgency=Urgency.LOW,
            attention_score=0.9,
            stress_indicators=stress_indicators,
            confidence=0.95,
            metadata=metadata
        )
        
        assert token.metadata is not None
        assert token.metadata["frames_processed"] == 90
        assert token.metadata["processing_time_ms"] == 245


class TestBiometricAnalysisRequest:
    """Test BiometricAnalysisRequest model"""
    
    def test_valid_analysis_request(self):
        """Test creating a valid analysis request"""
        landmarks = [[0.1, 0.2, 0.3] for _ in range(468)]
        
        request = BiometricAnalysisRequest(
            session_id="sess_req123",
            landmarks=landmarks,
            frame_count=90,
            capture_duration=3.0
        )
        
        assert request.session_id == "sess_req123"
        assert len(request.landmarks) == 468
        assert request.frame_count == 90
        assert request.capture_duration == 3.0
        assert isinstance(request.timestamp, datetime)


class TestTeachingModule:
    """Test TeachingModule model"""
    
    def test_valid_teaching_module(self):
        """Test creating a valid teaching module"""
        module = TeachingModule(
            module_id="mod_001",
            type=ModuleType.EXPLANATION,
            title="Understanding React Hooks",
            content="React Hooks are functions that let you use state...",
            estimated_time=60,
            complexity=ComplexityLevel.INTERMEDIATE,
            order=0
        )
        
        assert module.module_id == "mod_001"
        assert module.type == ModuleType.EXPLANATION
        assert module.title == "Understanding React Hooks"
        assert module.estimated_time == 60
        assert module.complexity == ComplexityLevel.INTERMEDIATE
        assert module.interactive is False
    
    def test_teaching_module_with_code(self):
        """Test teaching module with code snippets"""
        code_snippets = [
            {
                "language": "javascript",
                "content": "const [state, setState] = useState(0);"
            }
        ]
        
        module = TeachingModule(
            module_id="mod_002",
            type=ModuleType.CODE_EXAMPLE,
            title="useState Example",
            content="Here's how to use useState...",
            estimated_time=45,
            complexity=ComplexityLevel.BEGINNER,
            interactive=True,
            code_snippets=code_snippets,
            order=1
        )
        
        assert module.interactive is True
        assert module.code_snippets is not None
        assert len(module.code_snippets) == 1
        assert module.code_snippets[0]["language"] == "javascript"


class TestSourceReference:
    """Test SourceReference model"""
    
    def test_valid_source_reference(self):
        """Test creating a valid source reference"""
        source = SourceReference(
            title="React Documentation",
            url="https://react.dev/reference/react/useState",
            relevance_score=0.95,
            excerpt="useState is a React Hook that lets you add state..."
        )
        
        assert source.title == "React Documentation"
        assert source.url == "https://react.dev/reference/react/useState"
        assert source.relevance_score == 0.95
        assert source.excerpt is not None


class TestKnowledgePayload:
    """Test KnowledgePayload model"""
    
    def test_valid_knowledge_payload(self):
        """Test creating a valid knowledge payload"""
        module1 = TeachingModule(
            module_id="mod_001",
            type=ModuleType.EXPLANATION,
            title="Introduction",
            content="Content here...",
            estimated_time=60,
            complexity=ComplexityLevel.INTERMEDIATE,
            order=0
        )
        
        module2 = TeachingModule(
            module_id="mod_002",
            type=ModuleType.CODE_EXAMPLE,
            title="Example",
            content="Example code...",
            estimated_time=90,
            complexity=ComplexityLevel.INTERMEDIATE,
            order=1
        )
        
        source = SourceReference(
            title="Documentation",
            relevance_score=0.9
        )
        
        payload = KnowledgePayload(
            session_id="sess_knowledge123",
            query="How to use React hooks?",
            core_concept="React Hooks",
            complexity_level=ComplexityLevel.INTERMEDIATE,
            teaching_modules=[module1, module2],
            related_concepts=["useState", "useEffect"],
            source_references=[source],
            total_estimated_time=150,
            keywords=["React", "Hooks", "State"]
        )
        
        assert payload.session_id == "sess_knowledge123"
        assert payload.query == "How to use React hooks?"
        assert payload.core_concept == "React Hooks"
        assert len(payload.teaching_modules) == 2
        assert payload.total_estimated_time == 150
        assert len(payload.related_concepts) == 2
        assert len(payload.keywords) == 3
    
    def test_knowledge_payload_with_metadata(self):
        """Test knowledge payload with metadata"""
        module = TeachingModule(
            module_id="mod_001",
            type=ModuleType.QUICK_REFERENCE,
            title="Quick Ref",
            content="Quick reference...",
            estimated_time=30,
            complexity=ComplexityLevel.BEGINNER,
            order=0
        )
        
        metadata = {
            "search_time_ms": 1250,
            "sources_queried": 5,
            "rag_model": "ibm/granite-13b-chat-v2"
        }
        
        payload = KnowledgePayload(
            session_id="sess_meta123",
            query="Quick syntax lookup",
            core_concept="Syntax Reference",
            complexity_level=ComplexityLevel.BEGINNER,
            teaching_modules=[module],
            total_estimated_time=30,
            metadata=metadata
        )
        
        assert payload.metadata is not None
        assert payload.metadata["search_time_ms"] == 1250
        assert payload.metadata["rag_model"] == "ibm/granite-13b-chat-v2"


class TestRAGQueryRequest:
    """Test RAGQueryRequest model"""
    
    def test_valid_rag_query_request(self):
        """Test creating a valid RAG query request"""
        request = RAGQueryRequest(
            session_id="sess_rag123",
            query="Explain Python decorators",
            context="learning",
            max_sources=5,
            complexity_preference=ComplexityLevel.INTERMEDIATE
        )
        
        assert request.session_id == "sess_rag123"
        assert request.query == "Explain Python decorators"
        assert request.context == "learning"
        assert request.max_sources == 5
        assert request.complexity_preference == ComplexityLevel.INTERMEDIATE
    
    def test_rag_query_request_defaults(self):
        """Test RAG query request with defaults"""
        request = RAGQueryRequest(
            session_id="sess_rag456",
            query="Quick question"
        )
        
        assert request.max_sources == 5
        assert request.context is None
        assert request.complexity_preference is None


class TestRAGQueryResponse:
    """Test RAGQueryResponse model"""
    
    def test_valid_rag_query_response(self):
        """Test creating a valid RAG query response"""
        module = TeachingModule(
            module_id="mod_001",
            type=ModuleType.EXPLANATION,
            title="Test",
            content="Content",
            estimated_time=60,
            complexity=ComplexityLevel.INTERMEDIATE,
            order=0
        )
        
        payload = KnowledgePayload(
            session_id="sess_resp123",
            query="Test query",
            core_concept="Test Concept",
            complexity_level=ComplexityLevel.INTERMEDIATE,
            teaching_modules=[module],
            total_estimated_time=60
        )
        
        response = RAGQueryResponse(
            session_id="sess_resp123",
            knowledge_payload=payload,
            processing_time_ms=1500.5,
            success=True
        )
        
        assert response.session_id == "sess_resp123"
        assert response.success is True
        assert response.processing_time_ms == 1500.5
        assert response.error_message is None
    
    def test_rag_query_response_with_error(self):
        """Test RAG query response with error"""
        module = TeachingModule(
            module_id="mod_001",
            type=ModuleType.EXPLANATION,
            title="Test",
            content="Content",
            estimated_time=60,
            complexity=ComplexityLevel.INTERMEDIATE,
            order=0
        )
        
        payload = KnowledgePayload(
            session_id="sess_err123",
            query="Test query",
            core_concept="Test Concept",
            complexity_level=ComplexityLevel.INTERMEDIATE,
            teaching_modules=[module],
            total_estimated_time=60
        )
        
        response = RAGQueryResponse(
            session_id="sess_err123",
            knowledge_payload=payload,
            processing_time_ms=500.0,
            success=False,
            error_message="API timeout"
        )
        
        assert response.success is False
        assert response.error_message == "API timeout"


# Made with Bob