"""
Biometric Analyzer Service
Processes facial landmarks to compute cognitive load and stress indicators
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

from ..models.biometric_token import (
    BiometricToken,
    CognitiveLoad,
    Urgency,
    StressIndicators,
    EmotionScores,
    BiometricAnalysisRequest
)

logger = logging.getLogger(__name__)


class BiometricAnalyzer:
    """
    Analyzes facial landmarks to determine cognitive load and stress levels
    Uses MediaPipe Face Mesh landmarks (468 points)
    """
    
    # Eye landmark indices for Eye Aspect Ratio calculation
    LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
    
    # Mouth landmark indices for tension detection
    MOUTH_INDICES = [61, 291, 0, 17, 269, 405]
    
    # Eyebrow landmark indices for expression analysis
    LEFT_EYEBROW_INDICES = [70, 63, 105, 66, 107]
    RIGHT_EYEBROW_INDICES = [300, 293, 334, 296, 336]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the biometric analyzer
        
        Args:
            config: Configuration dictionary with thresholds
        """
        self.config = config or {}
        self.high_load_threshold = self.config.get('high_load_threshold', 0.7)
        self.low_load_threshold = self.config.get('low_load_threshold', 0.3)
        
        logger.info("BiometricAnalyzer initialized")
    
    def analyze(self, request: BiometricAnalysisRequest) -> BiometricToken:
        """
        Main analysis method - processes landmarks and generates biometric token
        
        Args:
            request: BiometricAnalysisRequest containing landmarks and metadata
            
        Returns:
            BiometricToken with complete analysis
        """
        start_time = datetime.utcnow()
        
        try:
            # Convert landmarks to numpy array for processing
            landmarks_array = np.array(request.landmarks)
            
            # Calculate individual metrics
            ear = self._calculate_eye_aspect_ratio(landmarks_array)
            blink_rate = self._estimate_blink_rate(landmarks_array, request.capture_duration)
            gaze_stability = self._calculate_gaze_stability(landmarks_array)
            micro_tension = self._calculate_micro_tension(landmarks_array)
            head_pose_stability = self._calculate_head_pose_stability(landmarks_array)
            
            # Calculate attention score (composite metric)
            attention_score = self._calculate_attention_score(
                ear, gaze_stability, head_pose_stability
            )
            
            # Classify cognitive load
            cognitive_load = self._classify_cognitive_load(
                ear, blink_rate, gaze_stability, micro_tension
            )
            
            # Classify urgency
            urgency = self._classify_urgency(
                blink_rate, micro_tension, attention_score
            )
            
            # Calculate confidence in analysis
            confidence = self._calculate_confidence(
                request.frame_count, landmarks_array
            )
            
            # Create stress indicators
            stress_indicators = StressIndicators(
                blink_rate=blink_rate,
                gaze_stability=gaze_stability,
                micro_tension=micro_tension,
                eye_aspect_ratio=ear,
                head_pose_stability=head_pose_stability
            )
            
            # Optional: Emotion analysis (simplified for POC)
            emotion_scores = self._analyze_emotions(landmarks_array)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create biometric token
            token = BiometricToken(
                session_id=request.session_id,
                cognitive_load=cognitive_load,
                urgency=urgency,
                attention_score=attention_score,
                stress_indicators=stress_indicators,
                emotion_scores=emotion_scores,
                confidence=confidence,
                timestamp=request.timestamp,
                metadata={
                    "frames_processed": request.frame_count,
                    "processing_time_ms": processing_time,
                    "landmarks_detected": len(landmarks_array),
                    "capture_duration": request.capture_duration
                }
            )
            
            logger.info(
                f"Biometric analysis complete for session {request.session_id}: "
                f"cognitive_load={cognitive_load}, urgency={urgency}, "
                f"attention={attention_score:.2f}"
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Error in biometric analysis: {str(e)}", exc_info=True)
            raise
    
    def _calculate_eye_aspect_ratio(self, landmarks: np.ndarray) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) for attention tracking
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        
        Lower EAR indicates closed eyes or reduced attention
        """
        try:
            # Calculate for both eyes and average
            left_ear = self._compute_ear_for_eye(landmarks, self.LEFT_EYE_INDICES)
            right_ear = self._compute_ear_for_eye(landmarks, self.RIGHT_EYE_INDICES)
            
            return (left_ear + right_ear) / 2.0
        except Exception as e:
            logger.warning(f"Error calculating EAR: {e}")
            return 0.3  # Default moderate value
    
    def _compute_ear_for_eye(self, landmarks: np.ndarray, indices: List[int]) -> float:
        """Compute EAR for a single eye"""
        if len(landmarks.shape) == 3:
            # Average across frames
            landmarks = np.mean(landmarks, axis=0)
        
        # Get eye landmarks
        eye_points = landmarks[indices]
        
        # Vertical distances
        v1 = np.linalg.norm(eye_points[1] - eye_points[5])
        v2 = np.linalg.norm(eye_points[2] - eye_points[4])
        
        # Horizontal distance
        h = np.linalg.norm(eye_points[0] - eye_points[3])
        
        # EAR formula
        ear = (v1 + v2) / (2.0 * h) if h > 0 else 0.3
        
        return ear
    
    def _estimate_blink_rate(self, landmarks: np.ndarray, duration: float) -> float:
        """
        Estimate blinks per minute from EAR variations
        High blink rate can indicate stress or fatigue
        """
        try:
            if len(landmarks.shape) != 3:
                return 15.0  # Default normal blink rate
            
            # Calculate EAR for each frame
            ear_sequence = []
            for frame in landmarks:
                left_ear = self._compute_ear_for_eye(frame, self.LEFT_EYE_INDICES)
                right_ear = self._compute_ear_for_eye(frame, self.RIGHT_EYE_INDICES)
                ear_sequence.append((left_ear + right_ear) / 2.0)
            
            # Detect blinks (EAR drops below threshold)
            ear_array = np.array(ear_sequence)
            blink_threshold = 0.2
            blinks = np.sum(ear_array < blink_threshold)
            
            # Convert to blinks per minute
            blinks_per_minute = (blinks / duration) * 60 if duration > 0 else 15.0
            
            return min(blinks_per_minute, 100.0)  # Cap at 100
            
        except Exception as e:
            logger.warning(f"Error estimating blink rate: {e}")
            return 15.0
    
    def _calculate_gaze_stability(self, landmarks: np.ndarray) -> float:
        """
        Calculate gaze stability from eye position variance
        Higher stability indicates better focus
        """
        try:
            if len(landmarks.shape) != 3:
                return 0.8  # Default good stability
            
            # Use eye center positions across frames
            left_eye_centers = []
            right_eye_centers = []
            
            for frame in landmarks:
                left_center = np.mean(frame[self.LEFT_EYE_INDICES], axis=0)
                right_center = np.mean(frame[self.RIGHT_EYE_INDICES], axis=0)
                left_eye_centers.append(left_center)
                right_eye_centers.append(right_center)
            
            # Calculate variance
            left_variance = np.var(left_eye_centers, axis=0).sum()
            right_variance = np.var(right_eye_centers, axis=0).sum()
            
            # Convert variance to stability score (inverse relationship)
            avg_variance = (left_variance + right_variance) / 2.0
            stability = 1.0 / (1.0 + avg_variance * 100)  # Normalize
            
            return float(np.clip(stability, 0.0, 1.0))
            
        except Exception as e:
            logger.warning(f"Error calculating gaze stability: {e}")
            return 0.8
    
    def _calculate_micro_tension(self, landmarks: np.ndarray) -> float:
        """
        Calculate facial micro-tension from mouth and eyebrow positions
        Higher tension indicates stress
        """
        try:
            if len(landmarks.shape) == 3:
                landmarks = np.mean(landmarks, axis=0)
            
            # Mouth tension (distance between corners)
            mouth_points = landmarks[self.MOUTH_INDICES]
            mouth_width = np.linalg.norm(mouth_points[0] - mouth_points[1])
            mouth_height = np.linalg.norm(mouth_points[2] - mouth_points[3])
            mouth_ratio = mouth_height / mouth_width if mouth_width > 0 else 0.5
            
            # Eyebrow tension (elevation)
            left_brow = np.mean(landmarks[self.LEFT_EYEBROW_INDICES], axis=0)
            right_brow = np.mean(landmarks[self.RIGHT_EYEBROW_INDICES], axis=0)
            left_eye = np.mean(landmarks[self.LEFT_EYE_INDICES], axis=0)
            right_eye = np.mean(landmarks[self.RIGHT_EYE_INDICES], axis=0)
            
            left_elevation = left_brow[1] - left_eye[1]
            right_elevation = right_brow[1] - right_eye[1]
            avg_elevation = (left_elevation + right_elevation) / 2.0
            
            # Combine metrics (normalized)
            tension = (mouth_ratio * 0.5) + (abs(avg_elevation) * 0.5)
            
            return float(np.clip(tension, 0.0, 1.0))
            
        except Exception as e:
            logger.warning(f"Error calculating micro-tension: {e}")
            return 0.5
    
    def _calculate_head_pose_stability(self, landmarks: np.ndarray) -> float:
        """
        Calculate head pose stability from nose position variance
        """
        try:
            if len(landmarks.shape) != 3:
                return 0.8
            
            # Use nose tip (landmark 1) as reference
            nose_positions = landmarks[:, 1, :]
            variance = np.var(nose_positions, axis=0).sum()
            
            # Convert to stability score
            stability = 1.0 / (1.0 + variance * 50)
            
            return float(np.clip(stability, 0.0, 1.0))
            
        except Exception as e:
            logger.warning(f"Error calculating head pose stability: {e}")
            return 0.8
    
    def _calculate_attention_score(
        self, 
        ear: float, 
        gaze_stability: float, 
        head_pose_stability: float
    ) -> float:
        """
        Calculate composite attention score
        """
        # Weighted combination
        attention = (
            ear * 0.4 +
            gaze_stability * 0.4 +
            head_pose_stability * 0.2
        )
        
        return float(np.clip(attention, 0.0, 1.0))
    
    def _classify_cognitive_load(
        self,
        ear: float,
        blink_rate: float,
        gaze_stability: float,
        micro_tension: float
    ) -> CognitiveLoad:
        """
        Classify cognitive load based on multiple metrics
        """
        # Calculate composite stress score
        stress_score = 0.0
        
        # Low EAR indicates fatigue/high load
        if ear < 0.2:
            stress_score += 0.3
        elif ear < 0.25:
            stress_score += 0.15
        
        # High blink rate indicates stress
        if blink_rate > 25:
            stress_score += 0.25
        elif blink_rate > 20:
            stress_score += 0.15
        
        # Low gaze stability indicates distraction/high load
        if gaze_stability < 0.6:
            stress_score += 0.25
        elif gaze_stability < 0.75:
            stress_score += 0.15
        
        # High micro-tension indicates stress
        if micro_tension > 0.7:
            stress_score += 0.2
        elif micro_tension > 0.5:
            stress_score += 0.1
        
        # Classify based on thresholds
        if stress_score >= self.high_load_threshold:
            return CognitiveLoad.HIGH
        elif stress_score <= self.low_load_threshold:
            return CognitiveLoad.LOW
        else:
            return CognitiveLoad.MEDIUM
    
    def _classify_urgency(
        self,
        blink_rate: float,
        micro_tension: float,
        attention_score: float
    ) -> Urgency:
        """
        Classify urgency level based on stress indicators
        """
        urgency_score = 0.0
        
        # High blink rate suggests urgency
        if blink_rate > 25:
            urgency_score += 0.4
        elif blink_rate > 18:
            urgency_score += 0.2
        
        # High tension suggests urgency
        if micro_tension > 0.7:
            urgency_score += 0.4
        elif micro_tension > 0.5:
            urgency_score += 0.2
        
        # High attention suggests immediate need
        if attention_score > 0.8:
            urgency_score += 0.2
        
        # Classify
        if urgency_score >= 0.6:
            return Urgency.IMMEDIATE
        elif urgency_score >= 0.3:
            return Urgency.MODERATE
        else:
            return Urgency.LOW
    
    def _calculate_confidence(
        self,
        frame_count: int,
        landmarks: np.ndarray
    ) -> float:
        """
        Calculate confidence in the analysis based on data quality
        """
        confidence = 0.5  # Base confidence
        
        # More frames = higher confidence
        if frame_count >= 90:
            confidence += 0.3
        elif frame_count >= 60:
            confidence += 0.2
        elif frame_count >= 30:
            confidence += 0.1
        
        # Check landmark quality (variance indicates good tracking)
        if len(landmarks.shape) == 3 and landmarks.shape[0] > 1:
            variance = np.var(landmarks, axis=0).mean()
            if 0.001 < variance < 0.1:  # Good variance range
                confidence += 0.2
        
        return float(np.clip(confidence, 0.0, 1.0))
    
    def _analyze_emotions(self, landmarks: np.ndarray) -> EmotionScores:
        """
        Simplified emotion analysis for POC
        In production, would use dedicated emotion recognition model
        """
        # Placeholder implementation
        # In real system, integrate with emotion recognition model
        return EmotionScores(
            neutral=0.6,
            happy=0.1,
            sad=0.05,
            angry=0.05,
            fearful=0.1,
            disgusted=0.05,
            surprised=0.05
        )

# Made with Bob
