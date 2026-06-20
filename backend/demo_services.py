"""
Demo Script - Test All Services
Demonstrates that the backend services can run and produce output
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.biometric_analyzer import BiometricAnalyzer
from app.services.rag_engine import RAGEngine
from app.services.ui_orchestrator import UIOrchestrator
from app.models.biometric_token import (
    BiometricAnalysisRequest,
    CognitiveLoad,
    Urgency
)
from app.models.knowledge_payload import (
    RAGQueryRequest,
    ComplexityLevel
)
import numpy as np
from datetime import datetime


def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def demo_biometric_analyzer():
    """Demonstrate BiometricAnalyzer service"""
    print_section("1. BIOMETRIC ANALYZER SERVICE")
    
    # Initialize analyzer
    analyzer = BiometricAnalyzer()
    print("✓ BiometricAnalyzer initialized")
    
    # Create sample landmarks (simulating MediaPipe output)
    # Shape: (frames, landmarks, coordinates)
    num_frames = 90
    num_landmarks = 468
    landmarks = np.random.rand(num_frames, num_landmarks, 3) * 0.1 + 0.45
    
    # Add some variation to simulate real data
    landmarks[:, :, 0] += np.random.randn(num_frames, num_landmarks) * 0.01
    landmarks[:, :, 1] += np.random.randn(num_frames, num_landmarks) * 0.01
    
    print(f"✓ Generated sample landmarks: {landmarks.shape}")
    
    # Create analysis request
    request = BiometricAnalysisRequest(
        session_id="demo_session_001",
        landmarks=landmarks.tolist(),
        frame_count=num_frames,
        capture_duration=3.0,
        timestamp=datetime.utcnow()
    )
    
    # Analyze
    print("⏳ Analyzing biometric data...")
    token = analyzer.analyze(request)
    
    # Display results
    print("\n📊 BIOMETRIC ANALYSIS RESULTS:")
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
    
    return token


async def demo_rag_engine():
    """Demonstrate RAG Engine service"""
    print_section("2. RAG ENGINE SERVICE")
    
    # Initialize RAG engine (will use mock mode without credentials)
    engine = RAGEngine()
    print("✓ RAG Engine initialized (mock mode)")
    
    # Create query request
    request = RAGQueryRequest(
        session_id="demo_session_001",
        query="How do I use React hooks effectively?",
        max_sources=5,
        complexity_preference=ComplexityLevel.INTERMEDIATE
    )
    
    print(f"✓ Query: '{request.query}'")
    if request.complexity_preference:
        print(f"✓ Complexity: {request.complexity_preference.value}")
    
    # Execute query
    print("⏳ Synthesizing knowledge...")
    response = await engine.query(request)
    
    # Display results
    print("\n📚 KNOWLEDGE SYNTHESIS RESULTS:")
    print(f"   Success: {response.success}")
    print(f"   Processing Time: {response.processing_time_ms:.1f}ms")
    
    payload = response.knowledge_payload
    print(f"\n   Knowledge Payload:")
    print(f"      - Core Concept: {payload.core_concept}")
    print(f"      - Complexity: {payload.complexity_level.value}")
    print(f"      - Total Time: {payload.total_estimated_time}s")
    print(f"      - Modules: {len(payload.teaching_modules)}")
    
    print(f"\n   Teaching Modules:")
    for i, module in enumerate(payload.teaching_modules, 1):
        print(f"      {i}. {module.title}")
        print(f"         Type: {module.type.value}")
        print(f"         Time: {module.estimated_time}s")
        print(f"         Content: {module.content[:80]}...")
    
    if payload.keywords:
        print(f"\n   Keywords: {', '.join(payload.keywords)}")
    
    return payload


def demo_ui_orchestrator(biometric_token, knowledge_payload):
    """Demonstrate UI Orchestrator service"""
    print_section("3. UI ORCHESTRATOR SERVICE")
    
    # Initialize orchestrator
    orchestrator = UIOrchestrator()
    print("✓ UI Orchestrator initialized")
    
    # Orchestrate UI
    print("⏳ Generating dynamic UI configuration...")
    ui_config = orchestrator.orchestrate(biometric_token, knowledge_payload)
    
    # Display results
    print("\n🎨 UI CONFIGURATION RESULTS:")
    
    pres_config = ui_config['presentation_config']
    print(f"\n   Presentation Mode: {pres_config['mode'].upper()}")
    print(f"   Configuration:")
    print(f"      - Font Size: {pres_config['font_size']}")
    print(f"      - Max Words/Screen: {pres_config['max_words_per_screen']}")
    print(f"      - Animation Speed: {pres_config['animation_speed']}")
    print(f"      - Voice Enabled: {pres_config['voice_enabled']}")
    if pres_config['voice_enabled']:
        print(f"      - Voice Pace: {pres_config['voice_pace']}")
    print(f"      - Progressive Disclosure: {pres_config['progressive_disclosure']}")
    
    print(f"\n   Biometric Context:")
    bio_ctx = ui_config['biometric_context']
    print(f"      - Cognitive Load: {bio_ctx['cognitive_load']}")
    print(f"      - Urgency: {bio_ctx['urgency']}")
    print(f"      - Attention: {bio_ctx['attention_score']:.2f}")
    
    print(f"\n   Estimated Duration: {ui_config['estimated_duration']}s")
    
    # Show component tree structure
    comp_tree = ui_config['component_tree']
    print(f"\n   Component Tree:")
    print(f"      Root: {comp_tree['type']}")
    print(f"      Children: {len(comp_tree['children'])}")
    for child in comp_tree['children']:
        print(f"         - {child['type']} (id: {child['id']})")
        if 'children' in child and child['children']:
            print(f"           └─ {len(child['children'])} sub-components")
    
    return ui_config


def demo_integration():
    """Demonstrate full integration of all services"""
    print_section("4. FULL SERVICE INTEGRATION")
    
    print("🔄 Running complete pipeline:")
    print("   1. Biometric Analysis")
    print("   2. Knowledge Synthesis")
    print("   3. UI Orchestration")
    print()
    
    # Step 1: Biometric Analysis
    print("Step 1: Analyzing user's biometric state...")
    biometric_token = demo_biometric_analyzer()
    
    # Step 2: Knowledge Synthesis
    print("\nStep 2: Synthesizing knowledge based on query...")
    knowledge_payload = asyncio.run(demo_rag_engine())
    
    # Step 3: UI Orchestration
    print("\nStep 3: Generating adaptive UI...")
    ui_config = demo_ui_orchestrator(biometric_token, knowledge_payload)
    
    print_section("INTEGRATION SUMMARY")
    print("✅ All services executed successfully!")
    print(f"\n📊 Pipeline Results:")
    print(f"   • Biometric State: {biometric_token.cognitive_load.value} load, {biometric_token.urgency.value} urgency")
    print(f"   • Knowledge: {len(knowledge_payload.teaching_modules)} modules synthesized")
    print(f"   • UI Mode: {ui_config['presentation_config']['mode']}")
    print(f"   • Total Estimated Time: {ui_config['estimated_duration']}s")
    
    print(f"\n🎯 Adaptive Behavior:")
    if biometric_token.cognitive_load == CognitiveLoad.HIGH:
        print("   • High cognitive load detected")
        print("   • UI simplified with larger fonts")
        print("   • Voice narration enabled")
        print("   • Progressive disclosure activated")
    elif biometric_token.cognitive_load == CognitiveLoad.LOW:
        print("   • Low cognitive load detected")
        print("   • Detailed content provided")
        print("   • Code examples shown inline")
        print("   • Faster pacing enabled")
    else:
        print("   • Medium cognitive load detected")
        print("   • Balanced presentation mode")
        print("   • Moderate pacing and detail")


def main():
    """Main demo function"""
    print("\n" + "="*70)
    print("  EPHEMERAL INTENT SYNTHESIS SYSTEM - SERVICE DEMO")
    print("  IBM AI Builders Challenge - Proof of Concept")
    print("="*70)
    
    try:
        # Run full integration demo
        demo_integration()
        
        print("\n" + "="*70)
        print("  ✅ DEMO COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\n📝 Note: This demo runs in mock mode without IBM watsonx.ai credentials.")
        print("   For full functionality, configure WATSONX_API_KEY and WATSONX_PROJECT_ID.")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())


# Made with Bob