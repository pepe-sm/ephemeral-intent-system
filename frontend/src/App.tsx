/**
 * Main App Component
 * Ephemeral Intent Synthesis System - IBM AI Builders Challenge
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { BiometricCapture } from '@/components/BiometricCapture';
import { DynamicUIRenderer } from '@/components/DynamicUI/DynamicUIRenderer';
import { useAppStore, selectCurrentModule, selectIsCapturing } from '@/store/appStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { config } from '@/config';
import type { FaceLandmark, UIComponentTree } from '@/types';
import { Brain, Wifi, WifiOff, AlertCircle } from 'lucide-react';

function App() {
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [query, setQuery] = useState('');
  const [landmarksBuffer, setLandmarksBuffer] = useState<FaceLandmark[][]>([]);
  const [uiComponentTree, setUIComponentTree] = useState<UIComponentTree | null>(null);

  // Store state
  const {
    session,
    setSession,
    currentBiometricToken,
    knowledgePayload,
    isCapturingBiometrics,
    setIsCapturingBiometrics,
    currentModuleIndex,
    setCurrentModuleIndex,
    wsConnected,
    error,
    setError,
    completeModule,
  } = useAppStore();

  const currentModule = useAppStore(selectCurrentModule);

  // WebSocket connection
  const {
    connect,
    disconnect,
    sendFullPipeline,
    sendEngagementSignal,
    isConnected,
  } = useWebSocket({
    sessionId,
    autoConnect: true,
    onBiometricToken: (token) => {
      console.log('Biometric token received:', token);
    },
    onKnowledgePayload: (payload) => {
      console.log('Knowledge payload received:', payload);
    },
    onUIUpdate: (componentTree) => {
      console.log('UI update received:', componentTree);
      setUIComponentTree(componentTree);
      // Reset module index when new UI is received
      setCurrentModuleIndex(0);
    },
    onSessionComplete: () => {
      console.log('Session complete');
      setIsCapturingBiometrics(false);
    },
    onError: (err) => {
      console.error('WebSocket error:', err);
      setError(err.message);
    },
  });

  // Initialize session
  useEffect(() => {
    setSession({
      id: sessionId,
      status: 'initializing',
      created_at: new Date().toISOString(),
      current_module_index: 0,
      completed_modules: [],
    });
  }, [sessionId, setSession]);

  // Handle biometric capture completion
  const handleLandmarksDetected = useCallback(
    (landmarks: FaceLandmark[][]) => {
      console.log(`Captured ${landmarks.length} frames of biometric data`);
      setLandmarksBuffer(landmarks);
      setIsCapturingBiometrics(false);

      // Send full pipeline request if we have a query
      if (query.trim()) {
        sendFullPipeline(query, landmarks, landmarks.length);
        
        // Set a timeout to detect if pipeline gets stuck
        setTimeout(() => {
          if (!uiComponentTree && !error) {
            setError('Pipeline timeout - please try again or refresh the page');
          }
        }, 30000); // 30 second timeout
      }
    },
    [query, sendFullPipeline, setIsCapturingBiometrics, uiComponentTree, error, setError]
  );

  // Handle query submission
  const handleSubmitQuery = useCallback(() => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setError(null);
    setIsCapturingBiometrics(true);
  }, [query, setError, setIsCapturingBiometrics]);

  // Handle module completion
  const handleModuleComplete = useCallback(() => {
    if (currentModule) {
      completeModule(currentModule.module_id);
      sendEngagementSignal('understood');
    }
  }, [currentModule, completeModule, sendEngagementSignal]);

  // Handle need help
  const handleNeedHelp = useCallback(() => {
    sendEngagementSignal('confused');
    setError('Help requested - adjusting content...');
  }, [sendEngagementSignal, setError]);

  // Render connection status
  const renderConnectionStatus = () => (
    <div className="flex items-center gap-2">
      {wsConnected ? (
        <>
          <Wifi className="w-4 h-4 text-green-500" />
          <span className="text-sm text-green-600">Connected</span>
        </>
      ) : (
        <>
          <WifiOff className="w-4 h-4 text-red-500" />
          <span className="text-sm text-red-600">Disconnected</span>
        </>
      )}
    </div>
  );

  // Render error message
  const renderError = () => {
    if (!error) return null;

    return (
      <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="font-semibold text-red-900">Error</h4>
          <p className="text-sm text-red-700">{error}</p>
        </div>
        <button
          onClick={() => setError(null)}
          className="text-red-500 hover:text-red-700"
        >
          ×
        </button>
      </div>
    );
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Brain className="w-8 h-8 text-blue-600" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    Ephemeral Intent System
                  </h1>
                  <p className="text-sm text-gray-600">
                    AI-Powered Adaptive Learning
                  </p>
                </div>
              </div>
              {renderConnectionStatus()}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
          {renderError()}

          {/* Query Input Section */}
          {!knowledgePayload && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">What would you like to learn?</h2>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSubmitQuery()}
                  placeholder="e.g., How do React hooks work?"
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isCapturingBiometrics}
                />
                <button
                  onClick={handleSubmitQuery}
                  disabled={isCapturingBiometrics || !query.trim()}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {isCapturingBiometrics ? 'Analyzing...' : 'Start Learning'}
                </button>
              </div>
              <p className="mt-3 text-sm text-gray-600">
                We'll analyze your biometric signals to personalize the learning experience.
              </p>
            </div>
          )}

          {/* Biometric Capture Section */}
          {isCapturingBiometrics && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">Capturing Biometric Data</h2>
              <BiometricCapture
                onLandmarksDetected={handleLandmarksDetected}
                onError={(err) => setError(err.message)}
                isCapturing={isCapturingBiometrics}
                captureDuration={config.biometric_capture_duration}
                fps={config.biometric_fps}
                showVideo={true}
                showOverlay={true}
              />
            </div>
          )}

          {/* Biometric Token Display */}
          {currentBiometricToken && !isCapturingBiometrics && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h3 className="text-lg font-semibold mb-3">Biometric Analysis</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="text-sm text-gray-600">Cognitive Load</div>
                  <div className="text-lg font-semibold text-blue-900 capitalize">
                    {currentBiometricToken.cognitive_load}
                  </div>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <div className="text-sm text-gray-600">Attention</div>
                  <div className="text-lg font-semibold text-green-900">
                    {(currentBiometricToken.attention_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <div className="text-sm text-gray-600">Urgency</div>
                  <div className="text-lg font-semibold text-purple-900 capitalize">
                    {currentBiometricToken.urgency}
                  </div>
                </div>
                <div className="p-3 bg-orange-50 rounded-lg">
                  <div className="text-sm text-gray-600">Confidence</div>
                  <div className="text-lg font-semibold text-orange-900">
                    {(currentBiometricToken.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Loading State - Waiting for UI Generation */}
          {knowledgePayload && !uiComponentTree && !isCapturingBiometrics && (
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                <h3 className="text-xl font-semibold text-gray-900">
                  Generating Personalized Learning Experience
                </h3>
                <p className="text-gray-600">
                  Adapting content based on your cognitive state...
                </p>
                <div className="mt-4 p-3 bg-blue-50 rounded-lg flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                  <span className="text-sm text-blue-900">Voice guidance will be active</span>
                </div>
              </div>
            </div>
          )}

          {/* Knowledge Display with Dynamic UI */}
          {knowledgePayload && uiComponentTree && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <DynamicUIRenderer
                componentTree={uiComponentTree}
                currentModule={currentModule || undefined}
                cognitiveLoad={currentBiometricToken?.cognitive_load}
                onModuleComplete={handleModuleComplete}
                onNeedHelp={handleNeedHelp}
              />
            </div>
          )}

          {/* Progress Indicator */}
          {knowledgePayload && uiComponentTree && (
            <div className="mt-6 bg-white rounded-lg shadow-lg p-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="font-semibold">Learning Progress</span>
                <span>
                  {currentModuleIndex + 1} / {knowledgePayload.teaching_modules.length}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${((currentModuleIndex + 1) / knowledgePayload.teaching_modules.length) * 100}%`,
                  }}
                />
              </div>
            </div>
          )}

          {/* Retry Button for Stuck States */}
          {error && error.includes('timeout') && (
            <div className="mt-6 bg-white rounded-lg shadow-lg p-6 text-center">
              <button
                onClick={() => {
                  setError(null);
                  setUIComponentTree(null);
                  setIsCapturingBiometrics(false);
                  window.location.reload();
                }}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Restart Session
              </button>
            </div>
          )}

          {/* Debug Info (Development Only) */}
          {config.debug_mode && (
            <div className="mt-6 bg-gray-900 text-gray-100 rounded-lg p-4 text-xs font-mono">
              <div className="font-bold mb-2">Debug Info</div>
              <div>Session ID: {sessionId}</div>
              <div>Status: {session?.status}</div>
              <div>Frames Captured: {landmarksBuffer.length}</div>
              <div>Current Module: {currentModuleIndex + 1}</div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
            <p className="text-center text-sm text-gray-600">
              Ephemeral Intent Synthesis System - IBM AI Builders Challenge 2024
            </p>
            <p className="text-center text-xs text-gray-500 mt-1">
              Made with Bob
            </p>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
}

export default App;

// Made with Bob for IBM AI Builders Challenge