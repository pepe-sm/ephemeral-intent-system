"""
Standalone Biometric Analyzer Demo
Demonstrates facial analysis and cognitive load detection without RAG dependencies
"""

import sys
from pathlib import Path
import numpy as np
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.biometric_analyzer import BiometricAnalyzer
from app.models.biometric_token import (
    BiometricAnalysisRequest,
    CognitiveLoad,
    Urgency
)


def print_header(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_biometric_results(token):
    """Print biometric analysis results"""
    print("\n[BIOMETRIC ANALYSIS RESULTS]")
    print(f"   Session ID: {token.session_id}")
    print(f"   Cognitive Load: {token.cognitive_load.value.upper()}")
    print(f"   Urgency: {token.urgency.value.upper()}")
    print(f"   Attention Score: {token.attention_score:.2f}")
    print(f"   Confidence: {token.confidence:.2f}")
    print(f"\n   Stress Indicators:")
    print(f"      - Blink Rate: {token.stress_indicators.blink_rate:.1f} blinks/min")
    print(f"      - Gaze Stability: {token.stress_indicators.gaze_stability:.2f}")
    print(f"      - Micro Tension: {token.stress_indicators.micro_tension:.2f}")
    print(f"      - Eye Aspect Ratio: {token.stress_indicators.eye_aspect_ratio:.2f}")
    print(f"      - Head Pose Stability: {token.stress_indicators.head_pose_stability:.2f}")
    
    if token.metadata:
        print(f"\n   Processing:")
        print(f"      - Frames Processed: {token.metadata.get('frames_processed')}")
        print(f"      - Processing Time: {token.metadata.get('processing_time_ms'):.1f}ms")


def generate_sample_landmarks(num_frames=90, scenario="normal"):
    """
    Generate sample facial landmarks for testing
    
    Args:
        num_frames: Number of frames to generate
        scenario: 'normal', 'high_stress', or 'low_stress'
    
    Returns:
        numpy array of shape (frames, 468, 3)
    """
    num_landmarks = 468
    landmarks = np.random.rand(num_frames, num_landmarks, 3) * 0.1 + 0.45
    
    if scenario == "high_stress":
        # Simulate high stress: more variation, lower EAR, higher blink rate
        landmarks[:, :, 0] += np.random.randn(num_frames, num_landmarks) * 0.03
        landmarks[:, :, 1] += np.random.randn(num_frames, num_landmarks) * 0.03
        # Simulate eye closure (lower y-coordinates for eye landmarks)
        eye_indices = list(range(33, 42)) + list(range(133, 142))
        for idx in eye_indices:
            landmarks[:, idx, 1] *= 0.8  # Reduce eye opening
    
    elif scenario == "low_stress":
        # Simulate low stress: less variation, stable gaze
        landmarks[:, :, 0] += np.random.randn(num_frames, num_landmarks) * 0.005
        landmarks[:, :, 1] += np.random.randn(num_frames, num_landmarks) * 0.005
    
    else:  # normal
        # Normal variation
        landmarks[:, :, 0] += np.random.randn(num_frames, num_landmarks) * 0.01
        landmarks[:, :, 1] += np.random.randn(num_frames, num_landmarks) * 0.01
    
    return landmarks


def demo_scenario(analyzer, scenario_name, scenario_type, session_id):
    """Run a single demo scenario"""
    print_header(f"SCENARIO: {scenario_name}")
    
    # Generate landmarks for this scenario
    num_frames = 90
    landmarks = generate_sample_landmarks(num_frames, scenario_type)
    
    print(f"[+] Generated {num_frames} frames of facial landmarks")
    print(f"[+] Scenario type: {scenario_type}")
    print(f"[+] Landmark shape: {landmarks.shape}")
    
    # Create analysis request
    request = BiometricAnalysisRequest(
        session_id=session_id,
        landmarks=landmarks.tolist(),
        frame_count=num_frames,
        capture_duration=3.0,
        timestamp=datetime.utcnow()
    )
    
    # Analyze
    print("\n[*] Analyzing biometric data...")
    token = analyzer.analyze(request)
    
    # Display results
    print_biometric_results(token)
    
    # Interpretation
    print("\n[INTERPRETATION]")
    if token.cognitive_load == CognitiveLoad.HIGH:
        print("   >> HIGH cognitive load detected")
        print("   >> Recommendation: Simplify UI, enable voice guidance")
    elif token.cognitive_load == CognitiveLoad.LOW:
        print("   >> LOW cognitive load detected")
        print("   >> Recommendation: Provide detailed content, enable exploration")
    else:
        print("   >> MEDIUM cognitive load detected")
        print("   >> Recommendation: Balanced presentation mode")
    
    return token


def main():
    """Main demo function"""
    print("\n" + "="*70)
    print("  BIOMETRIC ANALYZER - STANDALONE DEMO")
    print("  Ephemeral Intent Synthesis System")
    print("="*70)
    
    try:
        # Initialize analyzer
        print_header("INITIALIZATION")
        analyzer = BiometricAnalyzer()
        print("[+] BiometricAnalyzer initialized successfully")
        print("[+] Configuration: Default thresholds loaded")
        
        # Run different scenarios
        scenarios = [
            ("Normal User Session", "normal", "session_001"),
            ("High Stress Debugging", "high_stress", "session_002"),
            ("Relaxed Learning Mode", "low_stress", "session_003")
        ]
        
        results = []
        for scenario_name, scenario_type, session_id in scenarios:
            token = demo_scenario(analyzer, scenario_name, scenario_type, session_id)
            results.append((scenario_name, token))
        
        # Summary
        print_header("DEMO SUMMARY")
        print("\n[RESULTS COMPARISON]")
        print(f"{'Scenario':<30} {'Cognitive Load':<15} {'Urgency':<15} {'Attention':<10}")
        print("-" * 70)
        for scenario_name, token in results:
            print(f"{scenario_name:<30} {token.cognitive_load.value:<15} "
                  f"{token.urgency.value:<15} {token.attention_score:<10.2f}")
        
        print("\n" + "="*70)
        print("  [SUCCESS] DEMO COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\n[KEY FEATURES DEMONSTRATED]")
        print("  [+] Real-time facial landmark analysis")
        print("  [+] Cognitive load classification (High/Medium/Low)")
        print("  [+] Urgency detection (Immediate/Moderate/Low)")
        print("  [+] Attention score calculation")
        print("  [+] Stress indicator metrics")
        print("  [+] Adaptive recommendations")
        
        print("\n[NEXT STEPS]")
        print("  1. Integrate with RAG engine for knowledge synthesis")
        print("  2. Connect to UI orchestrator for adaptive interfaces")
        print("  3. Deploy WebSocket endpoint for real-time streaming")
        print("  4. Build frontend with camera capture")
        print()
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())


# Made with Bob for IBM AI Builders Challenge