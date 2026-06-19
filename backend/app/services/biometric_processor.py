"""
Biometric Processor - Real-time MediaPipe Integration
Handles video stream processing and landmark extraction
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BiometricProcessor:
    """
    Real-time biometric data processor using MediaPipe Face Mesh
    Optimized for low-latency processing
    """
    
    def __init__(
        self,
        max_num_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        """
        Initialize MediaPipe Face Mesh processor
        
        Args:
            max_num_faces: Maximum number of faces to detect
            refine_landmarks: Whether to refine landmarks around eyes and lips
            min_detection_confidence: Minimum confidence for face detection
            min_tracking_confidence: Minimum confidence for landmark tracking
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=max_num_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        logger.info("BiometricProcessor initialized with MediaPipe Face Mesh")
    
    def process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Process a single video frame and extract facial landmarks
        
        Args:
            frame: BGR image from video capture
            
        Returns:
            Numpy array of shape (468, 3) with normalized landmarks or None
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = self.face_mesh.process(rgb_frame)
            
            if not results.multi_face_landmarks:
                return None
            
            # Extract first face landmarks
            face_landmarks = results.multi_face_landmarks[0]
            
            # Convert to numpy array
            landmarks = np.array([
                [lm.x, lm.y, lm.z]
                for lm in face_landmarks.landmark
            ])
            
            return landmarks
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None
    
    def process_video_stream(
        self,
        video_source: int = 0,
        duration_seconds: float = 3.0,
        target_fps: int = 30
    ) -> Tuple[List[np.ndarray], int, float]:
        """
        Process video stream for specified duration
        
        Args:
            video_source: Camera index or video file path
            duration_seconds: How long to capture
            target_fps: Target frames per second
            
        Returns:
            Tuple of (landmarks_list, frame_count, actual_duration)
        """
        cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {video_source}")
        
        # Set camera properties for performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, target_fps)
        
        landmarks_list = []
        frame_count = 0
        start_time = datetime.utcnow()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check duration
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= duration_seconds:
                    break
                
                # Process frame
                landmarks = self.process_frame(frame)
                if landmarks is not None:
                    landmarks_list.append(landmarks)
                    frame_count += 1
                
                # Optional: Display frame (for debugging)
                # cv2.imshow('Biometric Capture', frame)
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
            
            actual_duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Captured {frame_count} frames in {actual_duration:.2f}s "
                f"({frame_count/actual_duration:.1f} fps)"
            )
            
            return landmarks_list, frame_count, actual_duration
            
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def process_base64_frames(
        self,
        base64_frames: List[str]
    ) -> List[np.ndarray]:
        """
        Process frames received as base64 strings (from web frontend)
        
        Args:
            base64_frames: List of base64-encoded image strings
            
        Returns:
            List of landmark arrays
        """
        import base64
        
        landmarks_list = []
        
        for b64_frame in base64_frames:
            try:
                # Decode base64 to image
                img_data = base64.b64decode(b64_frame.split(',')[1] if ',' in b64_frame else b64_frame)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Process frame
                landmarks = self.process_frame(frame)
                if landmarks is not None:
                    landmarks_list.append(landmarks)
                    
            except Exception as e:
                logger.warning(f"Error processing base64 frame: {e}")
                continue
        
        return landmarks_list
    
    def draw_landmarks(
        self,
        frame: np.ndarray,
        landmarks: np.ndarray,
        draw_connections: bool = True
    ) -> np.ndarray:
        """
        Draw landmarks on frame for visualization
        
        Args:
            frame: BGR image
            landmarks: Normalized landmarks array
            draw_connections: Whether to draw mesh connections
            
        Returns:
            Frame with drawn landmarks
        """
        try:
            h, w = frame.shape[:2]
            
            # Convert normalized coordinates to pixel coordinates
            for landmark in landmarks:
                x = int(landmark[0] * w)
                y = int(landmark[1] * h)
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error drawing landmarks: {e}")
            return frame
    
    def optimize_landmarks_for_analysis(
        self,
        landmarks_list: List[np.ndarray]
    ) -> np.ndarray:
        """
        Optimize landmarks array for efficient analysis
        
        Args:
            landmarks_list: List of landmark arrays from multiple frames
            
        Returns:
            Optimized 3D array of shape (frames, 468, 3)
        """
        if not landmarks_list:
            raise ValueError("Empty landmarks list")
        
        # Stack into 3D array
        landmarks_array = np.stack(landmarks_list, axis=0)
        
        # Optional: Apply smoothing to reduce noise
        # Using simple moving average
        if len(landmarks_array) > 3:
            kernel_size = 3
            smoothed = np.zeros_like(landmarks_array)
            for i in range(len(landmarks_array)):
                start_idx = max(0, i - kernel_size // 2)
                end_idx = min(len(landmarks_array), i + kernel_size // 2 + 1)
                smoothed[i] = np.mean(landmarks_array[start_idx:end_idx], axis=0)
            landmarks_array = smoothed
        
        return landmarks_array
    
    def __del__(self):
        """Cleanup MediaPipe resources"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()


class OptimizedBiometricPipeline:
    """
    Optimized pipeline combining MediaPipe processing and biometric analysis
    Designed for low-latency real-time processing
    """
    
    def __init__(self):
        """Initialize the optimized pipeline"""
        from .biometric_analyzer import BiometricAnalyzer
        
        self.processor = BiometricProcessor()
        self.analyzer = BiometricAnalyzer()
        
        logger.info("OptimizedBiometricPipeline initialized")
    
    def process_and_analyze(
        self,
        video_source: int = 0,
        duration_seconds: float = 3.0,
        session_id: str = "default"
    ):
        """
        Complete pipeline: capture, process, and analyze
        
        Args:
            video_source: Camera index
            duration_seconds: Capture duration
            session_id: Session identifier
            
        Returns:
            BiometricToken with complete analysis
        """
        from ..models.biometric_token import BiometricAnalysisRequest
        
        # Capture and process video
        landmarks_list, frame_count, actual_duration = \
            self.processor.process_video_stream(video_source, duration_seconds)
        
        if not landmarks_list:
            raise RuntimeError("No landmarks detected in video stream")
        
        # Optimize landmarks
        landmarks_array = self.processor.optimize_landmarks_for_analysis(landmarks_list)
        
        # Create analysis request
        request = BiometricAnalysisRequest(
            session_id=session_id,
            landmarks=landmarks_array.tolist(),
            frame_count=frame_count,
            capture_duration=actual_duration,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Analyze
        token = self.analyzer.analyze(request)
        
        return token
    
    def process_web_frames_and_analyze(
        self,
        base64_frames: List[str],
        session_id: str,
        capture_duration: float
    ):
        """
        Process frames from web frontend and analyze
        
        Args:
            base64_frames: List of base64-encoded frames
            session_id: Session identifier
            capture_duration: Total capture duration
            
        Returns:
            BiometricToken with complete analysis
        """
        from ..models.biometric_token import BiometricAnalysisRequest
        
        # Process frames
        landmarks_list = self.processor.process_base64_frames(base64_frames)
        
        if not landmarks_list:
            raise RuntimeError("No landmarks detected in provided frames")
        
        # Optimize landmarks
        landmarks_array = self.processor.optimize_landmarks_for_analysis(landmarks_list)
        
        # Create analysis request
        request = BiometricAnalysisRequest(
            session_id=session_id,
            landmarks=landmarks_array.tolist(),
            frame_count=len(landmarks_list),
            capture_duration=capture_duration,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Analyze
        token = self.analyzer.analyze(request)
        
        return token


# Made with Bob