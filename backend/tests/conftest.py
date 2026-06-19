"""
Pytest Configuration and Shared Fixtures
Provides common test fixtures and setup for all tests
"""

import pytest
import numpy as np
from datetime import datetime
from typing import Dict, Any

from app.models.biometric_token import (
    BiometricToken,
    CognitiveLoad,
    Urgency,
    StressIndicators,
    EmotionScores,
    BiometricAnalysisRequest
)

from app.models.knowledge_payload import (
    KnowledgePayload,
    TeachingModule,
    SourceReference,
    ComplexityLevel,
    ModuleType
)


# ============================================================================
# Biometric Test Fixtures
# ============================================================================

@pytest.fixture
def sample_stress_indicators() -> StressIndicators:
    """Create sample stress indicators"""
    return StressIndicators(
        blink_rate=15.5,
        gaze_stability=0.85,
        micro_tension=0.45,
        eye_aspect_ratio=0.28,
        head_pose_stability=0.82
    )


@pytest.fixture
def sample_emotion_scores() -> EmotionScores:
    """Create sample emotion scores"""
    return EmotionScores(
        neutral=0.6,
        happy=0.2,
        sad=0.05,
        angry=0.05,
        fearful=0.05,
        disgusted=0.03,
        surprised=0.02
    )


@pytest.fixture
def sample_biometric_token(
    sample_stress_indicators: StressIndicators,
    sample_emotion_scores: EmotionScores
) -> BiometricToken:
    """Create sample biometric token"""
    return BiometricToken(
        session_id="test_session_001",
        cognitive_load=CognitiveLoad.MEDIUM,
        urgency=Urgency.MODERATE,
        attention_score=0.75,
        stress_indicators=sample_stress_indicators,
        emotion_scores=sample_emotion_scores,
        confidence=0.88,
        metadata={
            "frames_processed": 90,
            "processing_time_ms": 245,
            "landmarks_detected": 468
        }
    )


@pytest.fixture
def sample_biometric_request() -> BiometricAnalysisRequest:
    """Create sample biometric analysis request"""
    np.random.seed(42)
    landmarks = np.random.rand(90, 468, 3).tolist()
    
    return BiometricAnalysisRequest(
        session_id="test_request_001",
        landmarks=landmarks,
        frame_count=90,
        capture_duration=3.0
    )


# ============================================================================
# Knowledge Payload Test Fixtures
# ============================================================================

@pytest.fixture
def sample_teaching_module() -> TeachingModule:
    """Create sample teaching module"""
    return TeachingModule(
        module_id="mod_test_001",
        type=ModuleType.EXPLANATION,
        title="Test Module",
        content="This is test content for the module.",
        estimated_time=60,
        complexity=ComplexityLevel.INTERMEDIATE,
        interactive=False,
        order=0
    )


@pytest.fixture
def sample_code_module() -> TeachingModule:
    """Create sample code example module"""
    return TeachingModule(
        module_id="mod_test_002",
        type=ModuleType.CODE_EXAMPLE,
        title="Code Example",
        content="Example code implementation",
        estimated_time=90,
        complexity=ComplexityLevel.INTERMEDIATE,
        interactive=True,
        code_snippets=[
            {
                "language": "python",
                "content": "def example():\n    return 'Hello World'"
            }
        ],
        order=1
    )


@pytest.fixture
def sample_source_reference() -> SourceReference:
    """Create sample source reference"""
    return SourceReference(
        title="Test Documentation",
        url="https://example.com/docs",
        relevance_score=0.95,
        excerpt="This is a relevant excerpt from the documentation."
    )


@pytest.fixture
def sample_knowledge_payload(
    sample_teaching_module: TeachingModule,
    sample_code_module: TeachingModule,
    sample_source_reference: SourceReference
) -> KnowledgePayload:
    """Create sample knowledge payload"""
    return KnowledgePayload(
        session_id="test_knowledge_001",
        query="How to use Python decorators?",
        core_concept="Python Decorators",
        complexity_level=ComplexityLevel.INTERMEDIATE,
        teaching_modules=[sample_teaching_module, sample_code_module],
        related_concepts=["functions", "closures", "wrappers"],
        source_references=[sample_source_reference],
        total_estimated_time=150,
        keywords=["Python", "decorators", "functions"],
        metadata={
            "search_time_ms": 1250,
            "sources_queried": 5,
            "rag_model": "ibm/granite-13b-chat-v2"
        }
    )


# ============================================================================
# Landmark Generation Fixtures
# ============================================================================

@pytest.fixture
def generate_landmarks():
    """Factory fixture for generating test landmarks"""
    def _generate(
        num_frames: int = 90,
        num_points: int = 468,
        seed: int = 42,
        variance: float = 0.5
    ) -> np.ndarray:
        """
        Generate random facial landmarks for testing
        
        Args:
            num_frames: Number of frames to generate
            num_points: Number of landmark points (default 468 for MediaPipe)
            seed: Random seed for reproducibility
            variance: Variance in landmark positions
            
        Returns:
            numpy array of shape (num_frames, num_points, 3)
        """
        np.random.seed(seed)
        return np.random.rand(num_frames, num_points, 3) * variance + 0.25
    
    return _generate


@pytest.fixture
def generate_stable_landmarks():
    """Factory fixture for generating stable (low variance) landmarks"""
    def _generate(
        num_frames: int = 90,
        num_points: int = 468,
        seed: int = 42
    ) -> np.ndarray:
        """Generate landmarks with minimal variance (stable gaze)"""
        np.random.seed(seed)
        base = np.random.rand(num_points, 3) * 0.5 + 0.25
        landmarks = np.tile(base, (num_frames, 1, 1))
        # Add tiny variance
        landmarks += np.random.rand(num_frames, num_points, 3) * 0.01
        return landmarks
    
    return _generate


@pytest.fixture
def generate_high_stress_landmarks():
    """Factory fixture for generating high stress landmarks"""
    def _generate(
        num_frames: int = 90,
        num_points: int = 468,
        seed: int = 42
    ) -> np.ndarray:
        """Generate landmarks indicating high stress"""
        np.random.seed(seed)
        landmarks = np.random.rand(num_frames, num_points, 3) * 0.5 + 0.25
        
        # Simulate closed eyes (low EAR)
        eye_indices = list(range(33, 42)) + list(range(362, 371))
        for idx in eye_indices:
            landmarks[:, idx, 1] *= 0.3
        
        return landmarks
    
    return _generate


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def analyzer_config() -> Dict[str, Any]:
    """Default analyzer configuration"""
    return {
        'high_load_threshold': 0.7,
        'low_load_threshold': 0.3
    }


@pytest.fixture
def custom_analyzer_config() -> Dict[str, Any]:
    """Custom analyzer configuration for testing"""
    return {
        'high_load_threshold': 0.8,
        'low_load_threshold': 0.2
    }


# ============================================================================
# Session and Metadata Fixtures
# ============================================================================

@pytest.fixture
def test_session_id() -> str:
    """Generate test session ID"""
    return f"test_session_{datetime.utcnow().timestamp()}"


@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """Sample metadata dictionary"""
    return {
        "frames_processed": 90,
        "processing_time_ms": 245.5,
        "landmarks_detected": 468,
        "capture_duration": 3.0,
        "test_mode": True
    }


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "biometric: mark test as biometric analysis test"
    )
    config.addinivalue_line(
        "markers", "models: mark test as data model test"
    )
    config.addinivalue_line(
        "markers", "services: mark test as service layer test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add markers based on test file location
        if "test_models" in str(item.fspath):
            item.add_marker(pytest.mark.models)
            item.add_marker(pytest.mark.unit)
        elif "test_biometric_analyzer" in str(item.fspath):
            item.add_marker(pytest.mark.biometric)
            item.add_marker(pytest.mark.services)
            item.add_marker(pytest.mark.unit)


# Made with Bob