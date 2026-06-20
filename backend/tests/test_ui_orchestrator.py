"""
Unit tests for UI Orchestrator Service
Tests dynamic UI generation based on biometric context and cognitive load
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from app.services.ui_orchestrator import UIOrchestrator, PresentationMode
from app.models.biometric_token import (
    BiometricToken,
    StressIndicators,
    CognitiveLoad,
    Urgency
)
from app.models.knowledge_payload import (
    KnowledgePayload,
    TeachingModule,
    SourceReference,
    ComplexityLevel,
    ModuleType
)


# Fixtures

@pytest.fixture
def orchestrator():
    """Create UI Orchestrator instance"""
    return UIOrchestrator()


@pytest.fixture
def custom_orchestrator():
    """Create UI Orchestrator with custom config"""
    config = {
        'high_stress_threshold': 0.8,
        'low_attention_threshold': 0.3
    }
    return UIOrchestrator(config=config)


@pytest.fixture
def high_stress_token():
    """Biometric token with high stress"""
    return BiometricToken(
        session_id="test_high_stress",
        timestamp=datetime.utcnow(),
        stress_indicators=StressIndicators(
            eye_aspect_ratio=0.2,
            blink_rate=35.0,
            gaze_stability=0.3,
            micro_tension=0.8,
            head_pose_stability=0.4
        ),
        cognitive_load=CognitiveLoad.HIGH,
        urgency=Urgency.IMMEDIATE,
        attention_score=0.3,
        confidence=0.85
    )


@pytest.fixture
def low_stress_token():
    """Biometric token with low stress"""
    return BiometricToken(
        session_id="test_low_stress",
        timestamp=datetime.utcnow(),
        stress_indicators=StressIndicators(
            eye_aspect_ratio=0.35,
            blink_rate=15.0,
            gaze_stability=0.8,
            micro_tension=0.2,
            head_pose_stability=0.9
        ),
        cognitive_load=CognitiveLoad.LOW,
        urgency=Urgency.LOW,
        attention_score=0.85,
        confidence=0.9
    )


@pytest.fixture
def medium_stress_token():
    """Biometric token with medium stress"""
    return BiometricToken(
        session_id="test_medium_stress",
        timestamp=datetime.utcnow(),
        stress_indicators=StressIndicators(
            eye_aspect_ratio=0.28,
            blink_rate=22.0,
            gaze_stability=0.6,
            micro_tension=0.5,
            head_pose_stability=0.7
        ),
        cognitive_load=CognitiveLoad.MEDIUM,
        urgency=Urgency.MODERATE,
        attention_score=0.6,
        confidence=0.8
    )


@pytest.fixture
def sample_knowledge_payload():
    """Sample knowledge payload"""
    modules = [
        TeachingModule(
            module_id="module_1",
            type=ModuleType.EXPLANATION,
            title="Introduction to Python",
            content="Python is a high-level programming language...",
            estimated_time=120,
            complexity=ComplexityLevel.BEGINNER,
            order=0
        ),
        TeachingModule(
            module_id="module_2",
            type=ModuleType.CODE_EXAMPLE,
            title="Variables and Data Types",
            content="Variables store data values...",
            estimated_time=180,
            complexity=ComplexityLevel.BEGINNER,
            order=1,
            code_snippets=[{"language": "python", "content": "x = 5\nname = 'Alice'"}]
        )
    ]
    
    sources = [
        SourceReference(
            title="Python Documentation",
            url="https://docs.python.org",
            relevance_score=0.95
        )
    ]
    
    return KnowledgePayload(
        session_id="test_session",
        query="What is Python?",
        core_concept="Python Programming Language",
        teaching_modules=modules,
        source_references=sources,
        complexity_level=ComplexityLevel.BEGINNER,
        total_estimated_time=300
    )


# Test Classes

class TestUIOrchestrator:
    """Test UIOrchestrator initialization and configuration"""
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test basic initialization"""
        assert orchestrator is not None
        assert orchestrator.high_stress_threshold == 0.7
        assert orchestrator.low_attention_threshold == 0.4
    
    def test_orchestrator_custom_config(self, custom_orchestrator):
        """Test initialization with custom config"""
        assert custom_orchestrator.high_stress_threshold == 0.8
        assert custom_orchestrator.low_attention_threshold == 0.3


class TestPresentationModeSelection:
    """Test presentation mode determination logic"""
    
    def test_voice_first_high_stress_immediate_urgency(
        self,
        orchestrator,
        high_stress_token
    ):
        """High stress + immediate urgency should select voice-first"""
        mode = orchestrator._determine_presentation_mode(high_stress_token)
        assert mode == PresentationMode.VOICE_FIRST
    
    def test_voice_first_low_attention(self, orchestrator):
        """Low attention should select voice-first"""
        token = BiometricToken(
            session_id="test",
            timestamp=datetime.utcnow(),
            stress_indicators=StressIndicators(
                eye_aspect_ratio=0.3,
                blink_rate=20.0,
                gaze_stability=0.5,
                micro_tension=0.4,
                head_pose_stability=0.6
            ),
            cognitive_load=CognitiveLoad.MEDIUM,
            urgency=Urgency.MODERATE,
            attention_score=0.3,  # Low attention
            confidence=0.8
        )
        mode = orchestrator._determine_presentation_mode(token)
        assert mode == PresentationMode.VOICE_FIRST
    
    def test_text_first_low_stress_high_attention(
        self,
        orchestrator,
        low_stress_token
    ):
        """Low stress + high attention should select text-first"""
        mode = orchestrator._determine_presentation_mode(low_stress_token)
        assert mode == PresentationMode.TEXT_FIRST
    
    def test_balanced_mode_medium_stress(
        self,
        orchestrator,
        medium_stress_token
    ):
        """Medium stress should select balanced mode"""
        mode = orchestrator._determine_presentation_mode(medium_stress_token)
        assert mode == PresentationMode.BALANCED


class TestPresentationConfig:
    """Test presentation configuration generation"""
    
    def test_high_cognitive_load_config(self, orchestrator, high_stress_token):
        """Test config for high cognitive load"""
        mode = PresentationMode.VOICE_FIRST
        config = orchestrator._generate_presentation_config(
            high_stress_token,
            mode
        )
        
        assert config["mode"] == mode
        assert config["voice_enabled"] is True
        assert config["progressive_disclosure"] is True
        assert config["max_words_per_screen"] == 50
        assert config["font_size"] == "large"
        assert config["animation_speed"] == "slow"
        assert config["voice_pace"] == "slow"
    
    def test_low_cognitive_load_config(self, orchestrator, low_stress_token):
        """Test config for low cognitive load"""
        mode = PresentationMode.TEXT_FIRST
        config = orchestrator._generate_presentation_config(
            low_stress_token,
            mode
        )
        
        assert config["mode"] == mode
        assert config["voice_enabled"] is False
        assert config["progressive_disclosure"] is False
        assert config["show_code_inline"] is True
        assert config["max_words_per_screen"] == 200
        assert config["font_size"] == "medium"
        assert config["animation_speed"] == "fast"
    
    def test_medium_cognitive_load_config(
        self,
        orchestrator,
        medium_stress_token
    ):
        """Test config for medium cognitive load"""
        mode = PresentationMode.BALANCED
        config = orchestrator._generate_presentation_config(
            medium_stress_token,
            mode
        )
        
        assert config["mode"] == mode
        assert config["voice_enabled"] is True
        assert config["progressive_disclosure"] is True
        assert config["max_words_per_screen"] == 100
        assert config["font_size"] == "medium"
        assert config["animation_speed"] == "medium"
        assert config["voice_pace"] == "normal"
    
    def test_low_attention_adjustments(self, orchestrator):
        """Test config adjustments for low attention"""
        token = BiometricToken(
            session_id="test",
            timestamp=datetime.utcnow(),
            stress_indicators=StressIndicators(
                eye_aspect_ratio=0.3,
                blink_rate=20.0,
                gaze_stability=0.5,
                micro_tension=0.4,
                head_pose_stability=0.6
            ),
            cognitive_load=CognitiveLoad.LOW,
            urgency=Urgency.LOW,
            attention_score=0.4,  # Low attention
            confidence=0.8
        )
        
        config = orchestrator._generate_presentation_config(
            token,
            PresentationMode.TEXT_FIRST
        )
        
        # Low attention should force slow animations and progressive disclosure
        assert config["animation_speed"] == "slow"
        assert config["progressive_disclosure"] is True


class TestComponentTreeGeneration:
    """Test component tree generation"""
    
    def test_component_tree_structure(
        self,
        orchestrator,
        sample_knowledge_payload,
        medium_stress_token
    ):
        """Test basic component tree structure"""
        config = {
            "mode": PresentationMode.BALANCED,
            "voice_enabled": True,
            "progressive_disclosure": True,
            "show_code_inline": False,
            "max_words_per_screen": 100,
            "font_size": "medium",
            "animation_speed": "medium",
            "voice_pace": "normal"
        }
        
        tree = orchestrator._generate_component_tree(
            sample_knowledge_payload,
            config,
            medium_stress_token
        )
        
        assert tree["id"] == "root"
        assert tree["type"] == "Container"
        assert "children" in tree
        assert len(tree["children"]) >= 2  # At least header and modules
    
    def test_header_component(
        self,
        orchestrator,
        sample_knowledge_payload
    ):
        """Test header component creation"""
        header = orchestrator._create_header_component(sample_knowledge_payload)
        
        assert header["id"] == "header"
        assert header["type"] == "Header"
        assert header["props"]["title"] == sample_knowledge_payload.core_concept
        assert header["props"]["complexity"] == ComplexityLevel.BEGINNER.value
    
    def test_modules_container(
        self,
        orchestrator,
        sample_knowledge_payload,
        medium_stress_token
    ):
        """Test modules container creation"""
        config = {
            "mode": PresentationMode.BALANCED,
            "voice_enabled": True,
            "progressive_disclosure": True,
            "show_code_inline": False,
            "max_words_per_screen": 100,
            "font_size": "medium",
            "animation_speed": "medium",
            "voice_pace": "normal"
        }
        
        container = orchestrator._create_modules_container(
            sample_knowledge_payload.teaching_modules,
            config,
            medium_stress_token
        )
        
        assert container["type"] == "ModulesContainer"
        assert len(container["children"]) == 2  # Two modules
    
    def test_navigation_component(self, orchestrator):
        """Test navigation component creation"""
        nav = orchestrator._create_navigation_component(3)
        
        assert nav["type"] == "Navigation"
        assert nav["props"]["totalModules"] == 3
    
    def test_sources_component(
        self,
        orchestrator,
        sample_knowledge_payload
    ):
        """Test sources component creation"""
        sources = orchestrator._create_sources_component(
            sample_knowledge_payload.source_references
        )
        
        assert sources["type"] == "SourceReferences"
        # Sources component should have children for each reference
        assert "children" in sources
    
    def test_sources_only_for_low_cognitive_load(
        self,
        orchestrator,
        sample_knowledge_payload,
        high_stress_token,
        low_stress_token
    ):
        """Test that sources are only shown for low cognitive load"""
        config = {
            "mode": PresentationMode.VOICE_FIRST,
            "voice_enabled": True,
            "progressive_disclosure": True,
            "show_code_inline": False,
            "max_words_per_screen": 50,
            "font_size": "large",
            "animation_speed": "slow",
            "voice_pace": "slow"
        }
        
        # High cognitive load - no sources
        tree_high = orchestrator._generate_component_tree(
            sample_knowledge_payload,
            config,
            high_stress_token
        )
        source_components_high = [
            c for c in tree_high["children"]
            if c["type"] == "SourceReferences"
        ]
        assert len(source_components_high) == 0
        
        # Low cognitive load - sources included
        tree_low = orchestrator._generate_component_tree(
            sample_knowledge_payload,
            config,
            low_stress_token
        )
        source_components_low = [
            c for c in tree_low["children"]
            if c["type"] == "SourceReferences"
        ]
        assert len(source_components_low) == 1


class TestOrchestration:
    """Test main orchestration method"""
    
    def test_orchestrate_complete_output(
        self,
        orchestrator,
        sample_knowledge_payload,
        medium_stress_token
    ):
        """Test complete orchestration output"""
        result = orchestrator.orchestrate(
            medium_stress_token,
            sample_knowledge_payload
        )
        
        # Check all required keys
        assert "component_tree" in result
        assert "presentation_config" in result
        assert "estimated_duration" in result
        assert "biometric_context" in result
        assert "timestamp" in result
        
        # Check biometric context
        context = result["biometric_context"]
        assert context["cognitive_load"] == CognitiveLoad.MEDIUM.value
        assert context["urgency"] == Urgency.MODERATE.value
        assert "attention_score" in context
    
    def test_orchestrate_high_stress_scenario(
        self,
        orchestrator,
        sample_knowledge_payload,
        high_stress_token
    ):
        """Test orchestration for high stress scenario"""
        result = orchestrator.orchestrate(
            high_stress_token,
            sample_knowledge_payload
        )
        
        config = result["presentation_config"]
        assert config["mode"] == PresentationMode.VOICE_FIRST
        assert config["voice_enabled"] is True
        assert config["max_words_per_screen"] == 50
        assert config["font_size"] == "large"
    
    def test_orchestrate_low_stress_scenario(
        self,
        orchestrator,
        sample_knowledge_payload,
        low_stress_token
    ):
        """Test orchestration for low stress scenario"""
        result = orchestrator.orchestrate(
            low_stress_token,
            sample_knowledge_payload
        )
        
        config = result["presentation_config"]
        assert config["mode"] == PresentationMode.TEXT_FIRST
        assert config["show_code_inline"] is True
        assert config["max_words_per_screen"] == 200
    
    def test_estimated_duration_calculation(
        self,
        orchestrator,
        sample_knowledge_payload,
        medium_stress_token
    ):
        """Test estimated duration calculation"""
        result = orchestrator.orchestrate(
            medium_stress_token,
            sample_knowledge_payload
        )
        
        # Should be based on knowledge payload total time
        assert result["estimated_duration"] > 0
        assert isinstance(result["estimated_duration"], (int, float))


# Engagement signal handling will be implemented in the WebSocket layer
# class TestEngagementSignalHandling:
#     """Test engagement signal handling"""
#     pass


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_modules_list(self, orchestrator, low_stress_token):
        """Test handling of empty teaching modules"""
        payload = KnowledgePayload(
            session_id="test_empty",
            query="test",
            core_concept="Test Concept",
            teaching_modules=[],
            source_references=[],
            complexity_level=ComplexityLevel.BEGINNER,
            total_estimated_time=0
        )
        
        result = orchestrator.orchestrate(low_stress_token, payload)
        assert result is not None
        assert "component_tree" in result
    
    def test_single_module(self, orchestrator, medium_stress_token):
        """Test with single teaching module"""
        module = TeachingModule(
            module_id="single",
            type=ModuleType.EXPLANATION,
            title="Single Module",
            content="Content",
            estimated_time=60,
            complexity=ComplexityLevel.BEGINNER,
            order=0
        )
        
        payload = KnowledgePayload(
            session_id="test_single",
            query="test",
            core_concept="Test",
            teaching_modules=[module],
            source_references=[],
            complexity_level=ComplexityLevel.BEGINNER,
            total_estimated_time=60
        )
        
        result = orchestrator.orchestrate(medium_stress_token, payload)
        tree = result["component_tree"]
        
        # Should not have navigation for single module
        nav_components = [
            c for c in tree["children"]
            if c["type"] == "Navigation"
        ]
        assert len(nav_components) == 0
    
    def test_extreme_attention_values(self, orchestrator):
        """Test with extreme attention score values"""
        # Very low attention
        token_low = BiometricToken(
            session_id="test",
            timestamp=datetime.utcnow(),
            stress_indicators=StressIndicators(
                eye_aspect_ratio=0.3,
                blink_rate=20.0,
                gaze_stability=0.5,
                micro_tension=0.4,
                head_pose_stability=0.6
            ),
            cognitive_load=CognitiveLoad.LOW,
            urgency=Urgency.LOW,
            attention_score=0.0,
            confidence=0.8
        )
        
        mode = orchestrator._determine_presentation_mode(token_low)
        assert mode == PresentationMode.VOICE_FIRST
        
        # Very high attention
        token_high = BiometricToken(
            session_id="test",
            timestamp=datetime.utcnow(),
            stress_indicators=StressIndicators(
                eye_aspect_ratio=0.35,
                blink_rate=15.0,
                gaze_stability=0.9,
                micro_tension=0.1,
                head_pose_stability=0.95
            ),
            cognitive_load=CognitiveLoad.LOW,
            urgency=Urgency.LOW,
            attention_score=1.0,
            confidence=0.95
        )
        
        mode = orchestrator._determine_presentation_mode(token_high)
        assert mode == PresentationMode.TEXT_FIRST

# Made with Bob
