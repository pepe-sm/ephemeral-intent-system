"""
Lifecycle Manager Service
Manages session lifecycle, engagement monitoring, and resource cleanup
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """Session status enumeration"""
    INITIALIZING = "initializing"
    CAPTURING_BIOMETRICS = "capturing_biometrics"
    ANALYZING = "analyzing"
    GENERATING_UI = "generating_ui"
    ACTIVE = "active"
    COMPLETING = "completing"
    TERMINATED = "terminated"
    ERROR = "error"


class EngagementLevel(str, Enum):
    """User engagement level"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DISENGAGED = "disengaged"


class Session:
    """Session data model"""
    
    def __init__(
        self,
        session_id: str,
        user_query: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.session_id = session_id
        self.user_query = user_query
        self.status = SessionStatus.INITIALIZING
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = self.created_at
        self.completed_at: Optional[datetime] = None
        
        # Session data
        self.biometric_token = None
        self.knowledge_payload = None
        self.ui_config = None
        
        # Progress tracking
        self.current_module_index = 0
        self.completed_modules: List[str] = []
        self.total_modules = 0
        
        # Engagement tracking
        self.engagement_level = EngagementLevel.MEDIUM
        self.engagement_signals: List[Dict] = []
        self.last_interaction = self.created_at
        
        # Metadata
        self.metadata: Dict = {}
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "user_query": self.user_query,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "current_module_index": self.current_module_index,
            "completed_modules": self.completed_modules,
            "total_modules": self.total_modules,
            "engagement_level": self.engagement_level.value,
            "metadata": self.metadata
        }


class LifecycleManager:
    """
    Manages session lifecycle from creation to termination
    Handles engagement monitoring and resource cleanup
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Lifecycle Manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Session storage (in-memory for POC, would use Redis in production)
        self.sessions: Dict[str, Session] = {}
        
        # Configuration
        self.session_timeout = self.config.get('session_timeout', 1800)  # 30 minutes
        self.engagement_check_interval = self.config.get('engagement_check_interval', 30)  # 30 seconds
        self.disengagement_threshold = self.config.get('disengagement_threshold', 120)  # 2 minutes
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
        
        logger.info("LifecycleManager initialized")
    
    def create_session(self, session_id: str, user_query: Optional[str] = None) -> Session:
        """
        Create a new session
        
        Args:
            session_id: Unique session identifier
            user_query: User's initial query
            
        Returns:
            Created Session object
        """
        if session_id in self.sessions:
            logger.warning(f"Session {session_id} already exists, returning existing")
            return self.sessions[session_id]
        
        session = Session(session_id=session_id, user_query=user_query)
        self.sessions[session_id] = session
        
        logger.info(f"Session created: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object or None if not found
        """
        return self.sessions.get(session_id)
    
    def update_session_status(self, session_id: str, status: SessionStatus) -> bool:
        """
        Update session status
        
        Args:
            session_id: Session identifier
            status: New status
            
        Returns:
            True if updated, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return False
        
        old_status = session.status
        session.status = status
        session.updated_at = datetime.utcnow()
        
        logger.info(f"Session {session_id} status: {old_status.value} -> {status.value}")
        
        # Handle status-specific actions
        if status == SessionStatus.TERMINATED:
            session.completed_at = datetime.utcnow()
            self._cleanup_session_resources(session_id)
        
        return True
    
    def update_session_data(
        self,
        session_id: str,
        biometric_token=None,
        knowledge_payload=None,
        ui_config=None
    ) -> bool:
        """
        Update session with service data
        
        Args:
            session_id: Session identifier
            biometric_token: BiometricToken from analyzer
            knowledge_payload: KnowledgePayload from RAG engine
            ui_config: UI configuration from orchestrator
            
        Returns:
            True if updated, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        if biometric_token:
            session.biometric_token = biometric_token
        
        if knowledge_payload:
            session.knowledge_payload = knowledge_payload
            session.total_modules = len(knowledge_payload.teaching_modules)
        
        if ui_config:
            session.ui_config = ui_config
        
        session.updated_at = datetime.utcnow()
        return True
    
    def record_engagement_signal(
        self,
        session_id: str,
        signal_type: str,
        data: Optional[Dict] = None
    ) -> bool:
        """
        Record user engagement signal
        
        Args:
            session_id: Session identifier
            signal_type: Type of engagement signal (understood, confused, etc.)
            data: Additional signal data
            
        Returns:
            True if recorded, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        signal = {
            "type": signal_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        session.engagement_signals.append(signal)
        session.last_interaction = datetime.utcnow()
        
        # Update engagement level based on signal
        self._update_engagement_level(session, signal_type)
        
        logger.info(f"Engagement signal recorded: {session_id} - {signal_type}")
        return True
    
    def _update_engagement_level(self, session: Session, signal_type: str):
        """Update engagement level based on signal"""
        # Positive signals
        if signal_type in ["understood", "next_module", "interaction"]:
            if session.engagement_level == EngagementLevel.LOW:
                session.engagement_level = EngagementLevel.MEDIUM
            elif session.engagement_level == EngagementLevel.MEDIUM:
                session.engagement_level = EngagementLevel.HIGH
        
        # Negative signals
        elif signal_type in ["confused", "need_help", "skip"]:
            if session.engagement_level == EngagementLevel.HIGH:
                session.engagement_level = EngagementLevel.MEDIUM
            elif session.engagement_level == EngagementLevel.MEDIUM:
                session.engagement_level = EngagementLevel.LOW
    
    def update_module_progress(
        self,
        session_id: str,
        module_id: str,
        completed: bool = True
    ) -> bool:
        """
        Update module completion progress
        
        Args:
            session_id: Session identifier
            module_id: Module identifier
            completed: Whether module is completed
            
        Returns:
            True if updated, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        if completed and module_id not in session.completed_modules:
            session.completed_modules.append(module_id)
            session.current_module_index += 1
            session.last_interaction = datetime.utcnow()
            
            logger.info(
                f"Module completed: {session_id} - {module_id} "
                f"({len(session.completed_modules)}/{session.total_modules})"
            )
            
            # Check if all modules completed
            if len(session.completed_modules) >= session.total_modules:
                self.update_session_status(session_id, SessionStatus.COMPLETING)
        
        return True
    
    def check_session_completion(self, session_id: str) -> bool:
        """
        Check if session should be completed
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session should be completed
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Check if all modules completed
        if session.total_modules > 0:
            if len(session.completed_modules) >= session.total_modules:
                return True
        
        # Check for explicit completion signal
        completion_signals = [
            s for s in session.engagement_signals
            if s["type"] == "complete"
        ]
        if completion_signals:
            return True
        
        return False
    
    async def monitor_engagement(self):
        """
        Background task to monitor session engagement
        Checks for inactive sessions and updates engagement levels
        """
        self._is_monitoring = True
        logger.info("Engagement monitoring started")
        
        try:
            while self._is_monitoring:
                await asyncio.sleep(self.engagement_check_interval)
                
                current_time = datetime.utcnow()
                
                for session_id, session in list(self.sessions.items()):
                    # Skip terminated sessions
                    if session.status == SessionStatus.TERMINATED:
                        continue
                    
                    # Check for timeout
                    time_since_creation = (current_time - session.created_at).total_seconds()
                    if time_since_creation > self.session_timeout:
                        logger.info(f"Session {session_id} timed out")
                        self.terminate_session(session_id, reason="timeout")
                        continue
                    
                    # Check for disengagement
                    time_since_interaction = (current_time - session.last_interaction).total_seconds()
                    if time_since_interaction > self.disengagement_threshold:
                        if session.engagement_level != EngagementLevel.DISENGAGED:
                            session.engagement_level = EngagementLevel.DISENGAGED
                            logger.warning(f"Session {session_id} disengaged")
                    
        except asyncio.CancelledError:
            logger.info("Engagement monitoring cancelled")
        except Exception as e:
            logger.error(f"Error in engagement monitoring: {e}", exc_info=True)
        finally:
            self._is_monitoring = False
    
    def start_monitoring(self):
        """Start background engagement monitoring"""
        if not self._monitoring_task or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self.monitor_engagement())
            logger.info("Engagement monitoring task started")
    
    def stop_monitoring(self):
        """Stop background engagement monitoring"""
        self._is_monitoring = False
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            logger.info("Engagement monitoring task stopped")
    
    def terminate_session(self, session_id: str, reason: str = "user_request") -> bool:
        """
        Terminate a session and cleanup resources
        
        Args:
            session_id: Session identifier
            reason: Termination reason
            
        Returns:
            True if terminated, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Update status
        self.update_session_status(session_id, SessionStatus.TERMINATED)
        
        # Store termination reason
        session.metadata["termination_reason"] = reason
        session.metadata["termination_time"] = datetime.utcnow().isoformat()
        
        logger.info(f"Session terminated: {session_id} (reason: {reason})")
        return True
    
    def _cleanup_session_resources(self, session_id: str):
        """
        Cleanup session resources
        
        Args:
            session_id: Session identifier
        """
        session = self.get_session(session_id)
        if not session:
            return
        
        # Clear large data objects to free memory
        session.biometric_token = None
        session.knowledge_payload = None
        session.ui_config = None
        
        logger.info(f"Session resources cleaned up: {session_id}")
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """
        Get session summary for export
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary dictionary or None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        duration = None
        if session.completed_at:
            duration = (session.completed_at - session.created_at).total_seconds()
        
        summary = {
            "session_id": session.session_id,
            "query": session.user_query,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "duration_seconds": duration,
            "modules_completed": len(session.completed_modules),
            "total_modules": session.total_modules,
            "engagement_level": session.engagement_level.value,
            "engagement_signals_count": len(session.engagement_signals),
            "metadata": session.metadata
        }
        
        # Add knowledge payload info if available
        if session.knowledge_payload:
            summary["core_concept"] = session.knowledge_payload.core_concept
            summary["keywords"] = session.knowledge_payload.keywords
            summary["related_concepts"] = session.knowledge_payload.related_concepts
        
        return summary
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        Remove old terminated sessions from memory
        
        Args:
            max_age_hours: Maximum age in hours for keeping sessions
        """
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if session.status == SessionStatus.TERMINATED:
                if session.completed_at and session.completed_at < cutoff_time:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            logger.info(f"Old session removed: {session_id}")
        
        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return sum(
            1 for s in self.sessions.values()
            if s.status not in [SessionStatus.TERMINATED, SessionStatus.ERROR]
        )
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all sessions as dictionaries"""
        return [session.to_dict() for session in self.sessions.values()]


# Made with Bob