/**
 * TypeScript Type Definitions
 * Shared types for the Ephemeral Intent Synthesis System frontend
 */

// ============================================================================
// Biometric Types
// ============================================================================

export type CognitiveLoad = 'high' | 'medium' | 'low';
export type Urgency = 'immediate' | 'moderate' | 'low';

export interface StressIndicators {
  blink_rate: number;
  gaze_stability: number;
  micro_tension: number;
  eye_aspect_ratio: number;
  head_pose_stability: number;
}

export interface EmotionScores {
  neutral: number;
  happy: number;
  sad: number;
  angry: number;
  fearful: number;
  disgusted: number;
  surprised: number;
}

export interface BiometricToken {
  session_id: string;
  cognitive_load: CognitiveLoad;
  urgency: Urgency;
  attention_score: number;
  stress_indicators: StressIndicators;
  emotion_scores?: EmotionScores;
  confidence: number;
  timestamp: string;
  metadata?: {
    frames_processed: number;
    processing_time_ms: number;
    landmarks_detected: number;
    capture_duration?: number;
  };
}

export interface BiometricUpdate {
  session_id: string;
  attention_score: number;
  cognitive_load: CognitiveLoad;
  timestamp: string;
}

// ============================================================================
// Knowledge & Content Types
// ============================================================================

export type ComplexityLevel = 'beginner' | 'intermediate' | 'advanced';
export type ModuleType = 
  | 'explanation' 
  | 'code_example' 
  | 'interactive_demo' 
  | 'visual_diagram' 
  | 'step_by_step' 
  | 'quick_reference';

export interface CodeSnippet {
  language: string;
  content: string;
}

export interface TeachingModule {
  module_id: string;
  type: ModuleType;
  title: string;
  content: string;
  estimated_time: number;
  complexity: ComplexityLevel;
  interactive: boolean;
  code_snippets?: CodeSnippet[];
  visual_aids?: string[];
  prerequisites?: string[];
  order: number;
}

export interface SourceReference {
  title: string;
  url?: string;
  relevance_score: number;
  excerpt?: string;
}

export interface KnowledgePayload {
  session_id: string;
  query: string;
  core_concept: string;
  complexity_level: ComplexityLevel;
  teaching_modules: TeachingModule[];
  related_concepts: string[];
  source_references: SourceReference[];
  total_estimated_time: number;
  keywords: string[];
  timestamp: string;
  metadata?: {
    search_time_ms: number;
    sources_queried: number;
    rag_model: string;
  };
}

// ============================================================================
// UI Orchestration Types
// ============================================================================

export interface PresentationConfig {
  mode: 'voice-first' | 'text-first' | 'balanced';
  max_words_per_screen: number;
  font_size: 'small' | 'medium' | 'large';
  animation_speed: 'slow' | 'medium' | 'fast';
  voice_enabled: boolean;
  voice_pace: 'slow' | 'normal' | 'fast';
  progressive_disclosure: boolean;
  show_code_inline: boolean;
}

export interface UIComponentTree {
  root: UIComponent;
  presentation_config: PresentationConfig;
}

export interface UIComponent {
  id: string;
  type: string;
  props: Record<string, any>;
  children?: UIComponent[];
}

// ============================================================================
// Session & WebSocket Types
// ============================================================================

export type SessionStatus = 
  | 'initializing' 
  | 'capturing_biometrics' 
  | 'analyzing' 
  | 'generating_ui' 
  | 'active' 
  | 'completing' 
  | 'terminated';

export interface Session {
  id: string;
  status: SessionStatus;
  created_at: string;
  biometric_token?: BiometricToken;
  knowledge_payload?: KnowledgePayload;
  ui_config?: PresentationConfig;
  current_module_index: number;
  completed_modules: string[];
}

export type WebSocketMessageType =
  | 'biometric_update'
  | 'user_query'
  | 'engagement_signal'
  | 'ui_update'
  | 'session_complete'
  | 'error';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp?: string;
}

export interface BiometricUpdateMessage extends WebSocketMessage {
  type: 'biometric_update';
  data: BiometricUpdate;
}

export interface UserQueryMessage extends WebSocketMessage {
  type: 'user_query';
  data: {
    text: string;
    context?: string;
  };
}

export interface EngagementSignalMessage extends WebSocketMessage {
  type: 'engagement_signal';
  data: {
    action: 'understood' | 'confused' | 'need_more' | 'complete';
  };
}

export interface UIUpdateMessage extends WebSocketMessage {
  type: 'ui_update';
  data: {
    component_tree: UIComponentTree;
    presentation_config: PresentationConfig;
    estimated_duration: number;
  };
}

export interface SessionCompleteMessage extends WebSocketMessage {
  type: 'session_complete';
  data: {
    summary: SessionSummary;
    download_url?: string;
  };
}

// ============================================================================
// Summary & Export Types
// ============================================================================

export interface SessionSummary {
  session_id: string;
  query: string;
  core_concept: string;
  duration_seconds: number;
  modules_completed: number;
  total_modules: number;
  key_learnings: string[];
  related_topics: string[];
  created_at: string;
  completed_at: string;
}

// ============================================================================
// MediaPipe Types
// ============================================================================

export interface FaceLandmark {
  x: number;
  y: number;
  z: number;
}

export interface FaceMeshResults {
  multiFaceLandmarks: FaceLandmark[][];
  image: HTMLCanvasElement | HTMLImageElement;
}

// ============================================================================
// Store Types (Zustand)
// ============================================================================

export interface AppState {
  // Session
  session: Session | null;
  setSession: (session: Session | null) => void;
  updateSessionStatus: (status: SessionStatus) => void;
  
  // Biometrics
  currentBiometricToken: BiometricToken | null;
  setBiometricToken: (token: BiometricToken | null) => void;
  
  // Knowledge
  knowledgePayload: KnowledgePayload | null;
  setKnowledgePayload: (payload: KnowledgePayload | null) => void;
  
  // UI State
  isCapturingBiometrics: boolean;
  setIsCapturingBiometrics: (capturing: boolean) => void;
  
  currentModuleIndex: number;
  setCurrentModuleIndex: (index: number) => void;
  
  // WebSocket
  wsConnected: boolean;
  setWsConnected: (connected: boolean) => void;
  
  // Error handling
  error: string | null;
  setError: (error: string | null) => void;
}

// ============================================================================
// Configuration Types
// ============================================================================

export interface AppConfig {
  backend_url: string;
  ws_url: string;
  biometric_capture_duration: number;
  biometric_fps: number;
  enable_voice_synthesis: boolean;
  debug_mode: boolean;
}

// Made with Bob
