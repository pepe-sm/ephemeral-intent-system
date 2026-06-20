"""
UI Orchestrator Service
Dynamically generates UI component trees based on biometric context and cognitive load
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.biometric_token import BiometricToken, CognitiveLoad, Urgency
from ..models.knowledge_payload import KnowledgePayload, TeachingModule, ModuleType

logger = logging.getLogger(__name__)


class PresentationMode:
    """Presentation mode configurations"""
    VOICE_FIRST = "voice-first"
    TEXT_FIRST = "text-first"
    BALANCED = "balanced"


class UIOrchestrator:
    """
    Orchestrates dynamic UI generation based on user's cognitive state
    Adapts presentation style, complexity, and interaction patterns
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize UI Orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Thresholds for UI adaptation
        self.high_stress_threshold = self.config.get('high_stress_threshold', 0.7)
        self.low_attention_threshold = self.config.get('low_attention_threshold', 0.4)
        
        logger.info("UIOrchestrator initialized")
    
    def orchestrate(
        self,
        biometric_token: BiometricToken,
        knowledge_payload: KnowledgePayload
    ) -> Dict[str, Any]:
        """
        Main orchestration method - generates complete UI configuration
        
        Args:
            biometric_token: User's biometric state
            knowledge_payload: Knowledge to present
            
        Returns:
            Complete UI configuration with component tree and presentation config
        """
        try:
            # Determine presentation mode based on cognitive load
            presentation_mode = self._determine_presentation_mode(biometric_token)
            
            # Generate presentation configuration
            presentation_config = self._generate_presentation_config(
                biometric_token,
                presentation_mode
            )
            
            # Generate component tree
            component_tree = self._generate_component_tree(
                knowledge_payload,
                presentation_config,
                biometric_token
            )
            
            # Calculate estimated duration
            estimated_duration = self._calculate_presentation_duration(
                knowledge_payload,
                presentation_config
            )
            
            return {
                "component_tree": component_tree,
                "presentation_config": presentation_config,
                "estimated_duration": estimated_duration,
                "biometric_context": {
                    "cognitive_load": biometric_token.cognitive_load.value,
                    "urgency": biometric_token.urgency.value,
                    "attention_score": biometric_token.attention_score
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in UI orchestration: {e}", exc_info=True)
            raise
    
    def _determine_presentation_mode(self, biometric_token: BiometricToken) -> str:
        """
        Determine optimal presentation mode based on cognitive state
        
        Args:
            biometric_token: User's biometric state
            
        Returns:
            Presentation mode string
        """
        cognitive_load = biometric_token.cognitive_load
        urgency = biometric_token.urgency
        attention_score = biometric_token.attention_score
        
        # High stress + high urgency = voice-first (minimal reading)
        if cognitive_load == CognitiveLoad.HIGH and urgency == Urgency.IMMEDIATE:
            return PresentationMode.VOICE_FIRST
        
        # Low attention = voice-first (help maintain focus)
        if attention_score < self.low_attention_threshold:
            return PresentationMode.VOICE_FIRST
        
        # Low stress + good attention = text-first (detailed learning)
        if cognitive_load == CognitiveLoad.LOW and attention_score > 0.7:
            return PresentationMode.TEXT_FIRST
        
        # Default to balanced mode
        return PresentationMode.BALANCED
    
    def _generate_presentation_config(
        self,
        biometric_token: BiometricToken,
        mode: str
    ) -> Dict[str, Any]:
        """
        Generate presentation configuration based on mode and biometric state
        
        Args:
            biometric_token: User's biometric state
            mode: Presentation mode
            
        Returns:
            Presentation configuration dictionary
        """
        cognitive_load = biometric_token.cognitive_load
        attention_score = biometric_token.attention_score
        
        # Base configuration
        config = {
            "mode": mode,
            "voice_enabled": mode in [PresentationMode.VOICE_FIRST, PresentationMode.BALANCED],
            "progressive_disclosure": cognitive_load != CognitiveLoad.LOW,
            "show_code_inline": cognitive_load == CognitiveLoad.LOW
        }
        
        # Adapt based on cognitive load
        if cognitive_load == CognitiveLoad.HIGH:
            config.update({
                "max_words_per_screen": 50,
                "font_size": "large",
                "animation_speed": "slow",
                "voice_pace": "slow"
            })
        elif cognitive_load == CognitiveLoad.MEDIUM:
            config.update({
                "max_words_per_screen": 100,
                "font_size": "medium",
                "animation_speed": "medium",
                "voice_pace": "normal"
            })
        else:  # LOW
            config.update({
                "max_words_per_screen": 200,
                "font_size": "medium",
                "animation_speed": "fast",
                "voice_pace": "normal"
            })
        
        # Adjust for attention level
        if attention_score < 0.5:
            config["animation_speed"] = "slow"
            config["progressive_disclosure"] = True
        
        return config
    
    def _generate_component_tree(
        self,
        knowledge_payload: KnowledgePayload,
        presentation_config: Dict[str, Any],
        biometric_token: BiometricToken
    ) -> Dict[str, Any]:
        """
        Generate hierarchical component tree for UI rendering
        
        Args:
            knowledge_payload: Knowledge to present
            presentation_config: Presentation configuration
            biometric_token: User's biometric state
            
        Returns:
            Component tree structure
        """
        # Root container
        root = {
            "id": "root",
            "type": "Container",
            "props": {
                "className": "ephemeral-session",
                "mode": presentation_config["mode"]
            },
            "children": []
        }
        
        # Add header with core concept
        header = self._create_header_component(knowledge_payload)
        root["children"].append(header)
        
        # Add teaching modules
        modules_container = self._create_modules_container(
            knowledge_payload.teaching_modules,
            presentation_config,
            biometric_token
        )
        root["children"].append(modules_container)
        
        # Add navigation/progress component
        if len(knowledge_payload.teaching_modules) > 1:
            navigation = self._create_navigation_component(
                len(knowledge_payload.teaching_modules)
            )
            root["children"].append(navigation)
        
        # Add source references (if low cognitive load)
        if biometric_token.cognitive_load == CognitiveLoad.LOW:
            sources = self._create_sources_component(
                knowledge_payload.source_references
            )
            root["children"].append(sources)
        
        return root
    
    def _create_header_component(self, knowledge_payload: KnowledgePayload) -> Dict[str, Any]:
        """Create header component with core concept"""
        return {
            "id": "header",
            "type": "Header",
            "props": {
                "title": knowledge_payload.core_concept,
                "complexity": knowledge_payload.complexity_level.value,
                "estimatedTime": knowledge_payload.total_estimated_time
            },
            "children": []
        }
    
    def _create_modules_container(
        self,
        modules: List[TeachingModule],
        presentation_config: Dict[str, Any],
        biometric_token: BiometricToken
    ) -> Dict[str, Any]:
        """Create container for teaching modules"""
        container = {
            "id": "modules-container",
            "type": "ModulesContainer",
            "props": {
                "progressive": presentation_config["progressive_disclosure"],
                "maxWordsPerScreen": presentation_config["max_words_per_screen"]
            },
            "children": []
        }
        
        # Add each module as a component
        for module in sorted(modules, key=lambda m: m.order):
            module_component = self._create_module_component(
                module,
                presentation_config,
                biometric_token
            )
            container["children"].append(module_component)
        
        return container
    
    def _create_module_component(
        self,
        module: TeachingModule,
        presentation_config: Dict[str, Any],
        biometric_token: BiometricToken
    ) -> Dict[str, Any]:
        """Create component for a single teaching module"""
        component = {
            "id": f"module-{module.module_id}",
            "type": self._map_module_type_to_component(module.type),
            "props": {
                "title": module.title,
                "content": self._adapt_content(
                    module.content,
                    presentation_config,
                    biometric_token
                ),
                "estimatedTime": module.estimated_time,
                "interactive": module.interactive,
                "complexity": module.complexity.value
            },
            "children": []
        }
        
        # Add code snippets if present
        if module.code_snippets and presentation_config["show_code_inline"]:
            for snippet in module.code_snippets:
                code_component = {
                    "id": f"code-{module.module_id}",
                    "type": "CodeSnippet",
                    "props": {
                        "language": snippet.get("language", "text"),
                        "content": snippet.get("content", ""),
                        "copyable": True
                    },
                    "children": []
                }
                component["children"].append(code_component)
        
        # Add voice narration if enabled
        if presentation_config["voice_enabled"]:
            component["props"]["voiceNarration"] = {
                "enabled": True,
                "pace": presentation_config["voice_pace"],
                "autoPlay": presentation_config["mode"] == PresentationMode.VOICE_FIRST
            }
        
        return component
    
    def _map_module_type_to_component(self, module_type: ModuleType) -> str:
        """Map module type to UI component type"""
        mapping = {
            ModuleType.EXPLANATION: "ExplanationModule",
            ModuleType.CODE_EXAMPLE: "CodeExampleModule",
            ModuleType.INTERACTIVE_DEMO: "InteractiveDemoModule",
            ModuleType.VISUAL_DIAGRAM: "VisualDiagramModule",
            ModuleType.STEP_BY_STEP: "StepByStepModule",
            ModuleType.QUICK_REFERENCE: "QuickReferenceModule"
        }
        return mapping.get(module_type, "GenericModule")
    
    def _adapt_content(
        self,
        content: str,
        presentation_config: Dict[str, Any],
        biometric_token: BiometricToken
    ) -> str:
        """
        Adapt content based on presentation config and cognitive state
        
        Args:
            content: Original content
            presentation_config: Presentation configuration
            biometric_token: User's biometric state
            
        Returns:
            Adapted content
        """
        # For high cognitive load, truncate and simplify
        if biometric_token.cognitive_load == CognitiveLoad.HIGH:
            max_words = presentation_config["max_words_per_screen"]
            words = content.split()
            if len(words) > max_words:
                content = " ".join(words[:max_words]) + "..."
        
        return content
    
    def _create_navigation_component(self, total_modules: int) -> Dict[str, Any]:
        """Create navigation/progress component"""
        return {
            "id": "navigation",
            "type": "Navigation",
            "props": {
                "totalModules": total_modules,
                "showProgress": True,
                "allowSkip": False
            },
            "children": []
        }
    
    def _create_sources_component(self, sources: List) -> Dict[str, Any]:
        """Create sources/references component"""
        return {
            "id": "sources",
            "type": "SourceReferences",
            "props": {
                "sources": [
                    {
                        "title": src.title,
                        "url": src.url,
                        "relevance": src.relevance_score
                    }
                    for src in sources
                ],
                "collapsible": True,
                "defaultCollapsed": True
            },
            "children": []
        }
    
    def _calculate_presentation_duration(
        self,
        knowledge_payload: KnowledgePayload,
        presentation_config: Dict[str, Any]
    ) -> int:
        """
        Calculate estimated presentation duration in seconds
        
        Args:
            knowledge_payload: Knowledge payload
            presentation_config: Presentation configuration
            
        Returns:
            Estimated duration in seconds
        """
        base_duration = knowledge_payload.total_estimated_time
        
        # Adjust for voice narration
        if presentation_config["voice_enabled"]:
            pace_multiplier = {
                "slow": 1.5,
                "normal": 1.2,
                "fast": 1.0
            }
            multiplier = pace_multiplier.get(
                presentation_config.get("voice_pace", "normal"),
                1.2
            )
            base_duration = int(base_duration * multiplier)
        
        # Adjust for progressive disclosure
        if presentation_config["progressive_disclosure"]:
            # Add time for transitions between modules
            base_duration += len(knowledge_payload.teaching_modules) * 5
        
        return base_duration
    
    def update_for_engagement(
        self,
        current_config: Dict[str, Any],
        engagement_signal: str
    ) -> Dict[str, Any]:
        """
        Update UI configuration based on engagement signals
        
        Args:
            current_config: Current UI configuration
            engagement_signal: Engagement signal (understood, confused, need_more, etc.)
            
        Returns:
            Updated UI configuration
        """
        updated_config = current_config.copy()
        
        if engagement_signal == "confused":
            # Simplify presentation
            updated_config["presentation_config"]["max_words_per_screen"] = 50
            updated_config["presentation_config"]["font_size"] = "large"
            updated_config["presentation_config"]["voice_enabled"] = True
            
        elif engagement_signal == "need_more":
            # Provide more detail
            updated_config["presentation_config"]["show_code_inline"] = True
            updated_config["presentation_config"]["progressive_disclosure"] = False
            
        elif engagement_signal == "understood":
            # Can move faster
            updated_config["presentation_config"]["animation_speed"] = "fast"
            updated_config["presentation_config"]["progressive_disclosure"] = False
        
        logger.info(f"Updated UI config for engagement signal: {engagement_signal}")
        return updated_config


# Made with Bob