"""
Unit Tests for Biometric Analyzer Service
Tests facial landmark analysis and cognitive load classification
"""

import pytest
import numpy as np
from datetime import datetime

from app.services.biometric_analyzer import BiometricAnalyzer
from app.models.biometric_token import (
    BiometricAnalysisRequest,
    BiometricToken,
    CognitiveLoad,
    Urgency
)


class TestBiometricAnalyzer:
    """Test BiometricAnalyzer service"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return BiometricAnalyzer()
    
    @pytest.fixture
    def sample_landmarks_single_frame(self):
        """Generate sample landmarks for a single frame (468 points x 3 coords)"""
        np.random.seed(42)
        return np.random.rand(468, 3) * 0.5 + 0.25
    
    @pytest.fixture
    def sample_landmarks_sequence(self):
        """Generate sample landmarks sequence (90 frames x 468 points x 3 coords)"""
        np.random.seed(42)
        return np.random.rand(90, 468, 3) * 0.5 + 0.25
    
    @pytest.fixture
    def high_stress_landmarks(self):
        """Generate landmarks indicating high stress (low EAR, high tension)"""
        np.random.seed(42)
        landmarks = np.random.rand(90, 468, 3) * 0.5 + 0.25
        
        # Simulate closed eyes (low EAR) by reducing vertical eye distances
        for eye_idx in BiometricAnalyzer.LEFT_EYE_INDICES + BiometricAnalyzer.RIGHT_EYE_INDICES:
            landmarks[:, eye_idx, 1] *= 0.3  # Reduce y-coordinate variance
        
        return landmarks
    
    @pytest.fixture
    def low_stress_landmarks(self):
        """Generate landmarks indicating low stress (good EAR, stable gaze)"""
        np.random.seed(42)
        landmarks = np.random.rand(90, 468, 3) * 0.1 + 0.4
        
        # Stable eye positions
        for eye_idx in BiometricAnalyzer.LEFT_EYE_INDICES + BiometricAnalyzer.RIGHT_EYE_INDICES:
            landmarks[:, eye_idx, :] = landmarks[0, eye_idx, :] + np.random.rand(90, 3) * 0.01
        
        return landmarks
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes correctly"""
        assert analyzer is not None
        assert analyzer.high_load_threshold == 0.7
        assert analyzer.low_load_threshold == 0.3
    
    def test_analyzer_custom_config(self):
        """Test analyzer with custom configuration"""
        config = {
            'high_load_threshold': 0.8,
            'low_load_threshold': 0.2
        }
        analyzer = BiometricAnalyzer(config=config)
        
        assert analyzer.high_load_threshold == 0.8
        assert analyzer.low_load_threshold == 0.2
    
    def test_analyze_basic_request(self, analyzer, sample_landmarks_sequence):
        """Test basic analysis with valid request"""
        request = BiometricAnalysisRequest(
            session_id="test_session_001",
            landmarks=sample_landmarks_sequence.tolist(),
            frame_count=90,
            capture_duration=3.0
        )
        
        token = analyzer.analyze(request)
        
        assert isinstance(token, BiometricToken)
        assert token.session_id == "test_session_001"
        assert isinstance(token.cognitive_load, CognitiveLoad)
        assert isinstance(token.urgency, Urgency)
        assert 0.0 <= token.attention_score <= 1.0
        assert 0.0 <= token.confidence <= 1.0
    
    def test_analyze_high_stress_scenario(self, analyzer, high_stress_landmarks):
        """Test analysis with high stress indicators"""
        request = BiometricAnalysisRequest(
            session_id="test_high_stress",
            landmarks=high_stress_landmarks.tolist(),
            frame_count=90,
            capture_duration=3.0
        )
        
        token = analyzer.analyze(request)
        
        # High stress should result in high or medium cognitive load
        assert token.cognitive_load in [CognitiveLoad.HIGH, CognitiveLoad.MEDIUM]
        # EAR is clamped to [0, 1]; confirm it is in valid range
        assert 0.0 <= token.stress_indicators.eye_aspect_ratio <= 1.0
    
    def test_analyze_low_stress_scenario(self, analyzer, low_stress_landmarks):
        """Test analysis with low stress indicators"""
        request = BiometricAnalysisRequest(
            session_id="test_low_stress",
            landmarks=low_stress_landmarks.tolist(),
            frame_count=90,
            capture_duration=3.0
        )
        
        token = analyzer.analyze(request)
        
        # Low stress should result in low/medium cognitive load
        assert token.cognitive_load in [CognitiveLoad.LOW, CognitiveLoad.MEDIUM]
        assert token.stress_indicators.gaze_stability > 0.5
    
    def test_calculate_eye_aspect_ratio(self, analyzer, sample_landmarks_single_frame):
        """Test EAR calculation"""
        ear = analyzer._calculate_eye_aspect_ratio(sample_landmarks_single_frame)
        
        assert isinstance(ear, float)
        assert 0.0 <= ear <= 1.0
    
    def test_calculate_eye_aspect_ratio_sequence(self, analyzer, sample_landmarks_sequence):
        """Test EAR calculation with frame sequence"""
        ear = analyzer._calculate_eye_aspect_ratio(sample_landmarks_sequence)
        
        assert isinstance(ear, float)
        assert 0.0 <= ear <= 1.0
    
    def test_estimate_blink_rate(self, analyzer, sample_landmarks_sequence):
        """Test blink rate estimation"""
        blink_rate = analyzer._estimate_blink_rate(sample_landmarks_sequence, 3.0)
        
        assert isinstance(blink_rate, float)
        assert 0.0 <= blink_rate <= 100.0
    
    def test_estimate_blink_rate_single_frame(self, analyzer, sample_landmarks_single_frame):
        """Test blink rate with single frame (should return default)"""
        blink_rate = analyzer._estimate_blink_rate(sample_landmarks_single_frame, 3.0)
        
        assert blink_rate == 15.0  # Default value
    
    def test_calculate_gaze_stability(self, analyzer, sample_landmarks_sequence):
        """Test gaze stability calculation"""
        stability = analyzer._calculate_gaze_stability(sample_landmarks_sequence)
        
        assert isinstance(stability, float)
        assert 0.0 <= stability <= 1.0
    
    def test_calculate_gaze_stability_stable_gaze(self, analyzer):
        """Test gaze stability with very stable gaze"""
        # Create landmarks with minimal variance
        stable_landmarks = np.ones((90, 468, 3)) * 0.5
        stable_landmarks += np.random.rand(90, 468, 3) * 0.001  # Tiny variance
        
        stability = analyzer._calculate_gaze_stability(stable_landmarks)
        
        assert stability > 0.9  # Should be very stable
    
    def test_calculate_gaze_stability_unstable_gaze(self, analyzer):
        """Test gaze stability with unstable gaze"""
        # Create landmarks with high variance
        unstable_landmarks = np.random.rand(90, 468, 3)
        
        stability = analyzer._calculate_gaze_stability(unstable_landmarks)
        
        assert stability < 0.7  # Should be less stable
    
    def test_calculate_micro_tension(self, analyzer, sample_landmarks_single_frame):
        """Test micro-tension calculation"""
        tension = analyzer._calculate_micro_tension(sample_landmarks_single_frame)
        
        assert isinstance(tension, float)
        assert 0.0 <= tension <= 1.0
    
    def test_calculate_micro_tension_sequence(self, analyzer, sample_landmarks_sequence):
        """Test micro-tension with frame sequence (should average)"""
        tension = analyzer._calculate_micro_tension(sample_landmarks_sequence)
        
        assert isinstance(tension, float)
        assert 0.0 <= tension <= 1.0
    
    def test_calculate_head_pose_stability(self, analyzer, sample_landmarks_sequence):
        """Test head pose stability calculation"""
        stability = analyzer._calculate_head_pose_stability(sample_landmarks_sequence)
        
        assert isinstance(stability, float)
        assert 0.0 <= stability <= 1.0
    
    def test_calculate_head_pose_stability_single_frame(self, analyzer, sample_landmarks_single_frame):
        """Test head pose stability with single frame"""
        stability = analyzer._calculate_head_pose_stability(sample_landmarks_single_frame)
        
        assert stability == 0.8  # Default value
    
    def test_calculate_attention_score(self, analyzer):
        """Test attention score calculation"""
        attention = analyzer._calculate_attention_score(
            ear=0.3,
            gaze_stability=0.8,
            head_pose_stability=0.85
        )
        
        assert isinstance(attention, float)
        assert 0.0 <= attention <= 1.0
    
    def test_calculate_attention_score_high_attention(self, analyzer):
        """Test attention score with high attention indicators"""
        attention = analyzer._calculate_attention_score(
            ear=0.35,
            gaze_stability=0.95,
            head_pose_stability=0.9
        )
        
        assert attention > 0.7
    
    def test_calculate_attention_score_low_attention(self, analyzer):
        """Test attention score with low attention indicators"""
        attention = analyzer._calculate_attention_score(
            ear=0.15,
            gaze_stability=0.4,
            head_pose_stability=0.5
        )
        
        assert attention < 0.5
    
    def test_classify_cognitive_load_high(self, analyzer):
        """Test cognitive load classification - high load"""
        load = analyzer._classify_cognitive_load(
            ear=0.15,  # Low EAR
            blink_rate=30.0,  # High blink rate
            gaze_stability=0.5,  # Low stability
            micro_tension=0.8  # High tension
        )
        
        assert load == CognitiveLoad.HIGH
    
    def test_classify_cognitive_load_medium(self, analyzer):
        """Test cognitive load classification - medium load"""
        # stress_score: ear=0.25 (+0.15) + blink_rate=22.0 (+0.15) +
        #               gaze_stability=0.7 (+0.15) + micro_tension=0.6 (+0.1) = 0.55
        # 0.3 < 0.55 < 0.7  →  MEDIUM
        load = analyzer._classify_cognitive_load(
            ear=0.25,
            blink_rate=22.0,
            gaze_stability=0.7,
            micro_tension=0.6
        )
        
        assert load == CognitiveLoad.MEDIUM
    
    def test_classify_cognitive_load_low(self, analyzer):
        """Test cognitive load classification - low load"""
        load = analyzer._classify_cognitive_load(
            ear=0.35,  # Good EAR
            blink_rate=12.0,  # Normal blink rate
            gaze_stability=0.9,  # High stability
            micro_tension=0.2  # Low tension
        )
        
        assert load == CognitiveLoad.LOW
    
    def test_classify_urgency_immediate(self, analyzer):
        """Test urgency classification - immediate"""
        urgency = analyzer._classify_urgency(
            blink_rate=30.0,
            micro_tension=0.8,
            attention_score=0.9
        )
        
        assert urgency == Urgency.IMMEDIATE
    
    def test_classify_urgency_moderate(self, analyzer):
        """Test urgency classification - moderate"""
        urgency = analyzer._classify_urgency(
            blink_rate=20.0,
            micro_tension=0.6,
            attention_score=0.7
        )
        
        assert urgency == Urgency.MODERATE
    
    def test_classify_urgency_low(self, analyzer):
        """Test urgency classification - low"""
        urgency = analyzer._classify_urgency(
            blink_rate=12.0,
            micro_tension=0.3,
            attention_score=0.5
        )
        
        assert urgency == Urgency.LOW
    
    def test_calculate_confidence_high_frames(self, analyzer, sample_landmarks_sequence):
        """Test confidence calculation with many frames"""
        confidence = analyzer._calculate_confidence(90, sample_landmarks_sequence)
        
        assert confidence >= 0.8  # Should be high with 90 frames
    
    def test_calculate_confidence_low_frames(self, analyzer, sample_landmarks_single_frame):
        """Test confidence calculation with few frames"""
        confidence = analyzer._calculate_confidence(10, sample_landmarks_single_frame)
        
        assert confidence < 0.8  # Should be lower with fewer frames
    
    def test_analyze_emotions(self, analyzer, sample_landmarks_single_frame):
        """Test emotion analysis"""
        emotions = analyzer._analyze_emotions(sample_landmarks_single_frame)
        
        assert emotions is not None
        assert 0.0 <= emotions.neutral <= 1.0
        assert 0.0 <= emotions.happy <= 1.0
        assert 0.0 <= emotions.sad <= 1.0
        assert 0.0 <= emotions.angry <= 1.0
    
    def test_biometric_token_metadata(self, analyzer, sample_landmarks_sequence):
        """Test that biometric token includes proper metadata"""
        request = BiometricAnalysisRequest(
            session_id="test_metadata",
            landmarks=sample_landmarks_sequence.tolist(),
            frame_count=90,
            capture_duration=3.0
        )
        
        token = analyzer.analyze(request)
        
        assert token.metadata is not None
        assert "frames_processed" in token.metadata
        assert "processing_time_ms" in token.metadata
        assert "landmarks_detected" in token.metadata
        assert "capture_duration" in token.metadata
        assert token.metadata["frames_processed"] == 90
        assert token.metadata["capture_duration"] == 3.0
    
    def test_stress_indicators_ranges(self, analyzer, sample_landmarks_sequence):
        """Test that all stress indicators are within valid ranges"""
        request = BiometricAnalysisRequest(
            session_id="test_ranges",
            landmarks=sample_landmarks_sequence.tolist(),
            frame_count=90,
            capture_duration=3.0
        )
        
        token = analyzer.analyze(request)
        indicators = token.stress_indicators
        
        assert 0.0 <= indicators.blink_rate <= 100.0
        assert 0.0 <= indicators.gaze_stability <= 1.0
        assert 0.0 <= indicators.micro_tension <= 1.0
        assert 0.0 <= indicators.eye_aspect_ratio <= 1.0
        assert 0.0 <= indicators.head_pose_stability <= 1.0
    
    def test_compute_ear_for_eye(self, analyzer, sample_landmarks_single_frame):
        """Test EAR computation for individual eye"""
        ear = analyzer._compute_ear_for_eye(
            sample_landmarks_single_frame,
            BiometricAnalyzer.LEFT_EYE_INDICES
        )
        
        assert isinstance(ear, float)
        assert 0.0 <= ear <= 1.0
    
    def test_error_handling_invalid_landmarks(self, analyzer):
        """Test that empty landmarks produce a token with safe defaults rather than crashing"""
        request = BiometricAnalysisRequest(
            session_id="test_error",
            landmarks=[],  # Empty landmarks
            frame_count=0,
            capture_duration=3.0
        )

        # Analyzer is resilient: returns a token with default/fallback values
        token = analyzer.analyze(request)
        assert token is not None
        assert token.session_id == "test_error"
        assert isinstance(token.cognitive_load, CognitiveLoad)
    
    def test_consistent_results(self, analyzer, sample_landmarks_sequence):
        """Test that analyzer produces consistent results for same input"""
        request = BiometricAnalysisRequest(
            session_id="test_consistency",
            landmarks=sample_landmarks_sequence.tolist(),
            frame_count=90,
            capture_duration=3.0
        )
        
        token1 = analyzer.analyze(request)
        token2 = analyzer.analyze(request)
        
        # Results should be identical for same input
        assert token1.cognitive_load == token2.cognitive_load
        assert token1.urgency == token2.urgency
        assert abs(token1.attention_score - token2.attention_score) < 0.01
        assert abs(token1.confidence - token2.confidence) < 0.01


class TestBiometricAnalyzerEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.fixture
    def analyzer(self):
        return BiometricAnalyzer()
    
    def test_minimal_landmarks(self, analyzer):
        """Test with minimal valid landmarks"""
        minimal_landmarks = np.random.rand(1, 468, 3)
        
        request = BiometricAnalysisRequest(
            session_id="test_minimal",
            landmarks=minimal_landmarks.tolist(),
            frame_count=1,
            capture_duration=0.033  # Single frame at 30fps
        )
        
        token = analyzer.analyze(request)
        assert token is not None
        assert token.confidence < 0.7  # Low confidence with single frame
    
    def test_maximum_landmarks(self, analyzer):
        """Test with maximum frame count"""
        max_landmarks = np.random.rand(300, 468, 3)  # 10 seconds at 30fps
        
        request = BiometricAnalysisRequest(
            session_id="test_maximum",
            landmarks=max_landmarks.tolist(),
            frame_count=300,
            capture_duration=10.0
        )
        
        token = analyzer.analyze(request)
        assert token is not None
        assert token.confidence > 0.8  # High confidence with many frames
    
    def test_zero_variance_landmarks(self, analyzer):
        """Test with completely static landmarks (no movement)"""
        static_landmarks = np.ones((90, 468, 3)) * 0.5
        
        request = BiometricAnalysisRequest(
            session_id="test_static",
            landmarks=static_landmarks.tolist(),
            frame_count=90,
            capture_duration=3.0
        )
        
        token = analyzer.analyze(request)
        assert token is not None
        # Static landmarks should indicate very stable gaze
        assert token.stress_indicators.gaze_stability > 0.9


# Made with Bob