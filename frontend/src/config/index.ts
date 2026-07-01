/**
 * Application Configuration
 * Environment-based configuration for the Ephemeral Intent System
 */

import type { AppConfig } from '@/types';

const isDevelopment = import.meta.env.MODE === 'development';
const isProduction = import.meta.env.MODE === 'production';

// Get environment variables with fallbacks
const getEnvVar = (key: string, defaultValue: string): string => {
  return import.meta.env[key] || defaultValue;
};

// Backend URL configuration
const BACKEND_HOST = getEnvVar('VITE_BACKEND_HOST', 'localhost');
const BACKEND_PORT = getEnvVar('VITE_BACKEND_PORT', '8000');
const BACKEND_PROTOCOL = getEnvVar('VITE_BACKEND_PROTOCOL', 'http');
const WS_PROTOCOL = getEnvVar('VITE_WS_PROTOCOL', 'ws');

// In development, use relative URLs to leverage Vite's proxy
// In production, use full URLs
const getBackendUrl = () => {
  if (isDevelopment) {
    return ''; // Use relative URLs in development (Vite proxy)
  }
  return `${BACKEND_PROTOCOL}://${BACKEND_HOST}:${BACKEND_PORT}`;
};

const getWsUrl = () => {
  if (isDevelopment) {
    // Use relative WebSocket URL to leverage Vite's proxy
    return `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;
  }
  return `${WS_PROTOCOL}://${BACKEND_HOST}:${BACKEND_PORT}/ws`;
};

export const config: AppConfig = {
  backend_url: getBackendUrl(),
  ws_url: getWsUrl(),
  biometric_capture_duration: parseInt(getEnvVar('VITE_BIOMETRIC_DURATION', '3'), 10),
  biometric_fps: parseInt(getEnvVar('VITE_BIOMETRIC_FPS', '30'), 10),
  enable_voice_synthesis: getEnvVar('VITE_ENABLE_VOICE', 'false') === 'true',
  debug_mode: isDevelopment,
};

// API endpoints
export const API_ENDPOINTS = {
  health: '/health',
  session: '/api/session',
  biometric: '/api/biometric',
  knowledge: '/api/knowledge',
  ui: '/api/ui',
};

// WebSocket message types
export const WS_MESSAGE_TYPES = {
  BIOMETRIC_ANALYSIS: 'biometric_analysis',
  KNOWLEDGE_QUERY: 'knowledge_query',
  FULL_PIPELINE: 'full_pipeline',
  ENGAGEMENT_SIGNAL: 'engagement_signal',
  BIOMETRIC_TOKEN: 'biometric_token',
  KNOWLEDGE_PAYLOAD: 'knowledge_payload',
  UI_UPDATE: 'ui_update',
  SESSION_COMPLETE: 'session_complete',
  PIPELINE_STATUS: 'pipeline_status',
  PIPELINE_COMPLETE: 'pipeline_complete',
  CONNECTION_ESTABLISHED: 'connection_established',
  ERROR: 'error',
  PING: 'ping',
  PONG: 'pong',
};

// Feature flags
export const FEATURES = {
  OFFLINE_MODE: getEnvVar('VITE_FEATURE_OFFLINE', 'false') === 'true',
  ANALYTICS: getEnvVar('VITE_FEATURE_ANALYTICS', 'false') === 'true',
  VOICE_SYNTHESIS: config.enable_voice_synthesis,
  DEBUG_PANEL: isDevelopment,
};

// Analytics configuration
export const ANALYTICS_CONFIG = {
  enabled: FEATURES.ANALYTICS,
  trackingId: getEnvVar('VITE_ANALYTICS_ID', ''),
  sampleRate: parseFloat(getEnvVar('VITE_ANALYTICS_SAMPLE_RATE', '1.0')),
};

// Logging configuration
export const LOG_CONFIG = {
  level: isDevelopment ? 'debug' : 'info',
  enableConsole: true,
  enableRemote: isProduction,
};

// Export environment info
export const ENV = {
  isDevelopment,
  isProduction,
  mode: import.meta.env.MODE,
};

// Validate configuration
export function validateConfig(): boolean {
  // In development, backend_url is intentionally empty (Vite proxy handles routing)
  // Only require ws_url to be set
  const required: (keyof AppConfig)[] = isDevelopment ? ['ws_url'] : ['backend_url', 'ws_url'];

  for (const key of required) {
    const value = config[key];
    if (value === undefined || value === null) {
      console.error(`Missing required config: ${key}`);
      return false;
    }
  }

  return true;
}

// Log configuration in development
if (isDevelopment) {
  console.log('App Configuration:', config);
  console.log('Features:', FEATURES);
  console.log('Environment:', ENV);
}

// Made with Bob for IBM AI Builders Challenge