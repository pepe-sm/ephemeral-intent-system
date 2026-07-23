/**
 * Main App Component — Student Lab Registration Flow
 * Ephemeral Intent Synthesis System
 *
 * Flow: Register / Login → Pick Topic → Learning Session → Complete
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { RegistrationPanel } from '@/components/RegistrationPanel';
import { TopicPanel } from '@/components/TopicPanel';
import { ResourcesPanel } from '@/components/ResourcesPanel';
import { VideoPlayer } from '@/components/VideoPlayer';
import { DynamicUIRenderer } from '@/components/DynamicUI/DynamicUIRenderer';
import { useAppStore, selectCurrentModule } from '@/store/appStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { config } from '@/config';
import type { UIComponentTree, StudentRegistration } from '@/types';
import { Brain, Wifi, WifiOff, AlertCircle, CheckCircle, LogOut, BookMarked } from 'lucide-react';

function App() {
  const [sessionId] = useState(
    () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );
  const [uiComponentTree, setUIComponentTree] = useState<UIComponentTree | null>(null);
  const [streamedModules, setStreamedModules] = useState<import('@/types').TeachingModule[]>([]);
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  // moduleId → video URL, populated as video_ready WS messages arrive
  const [moduleVideos,   setModuleVideos]   = useState<Record<string, string>>({});
  // moduleIds currently awaiting video generation (spinner shown until video_ready)
  const [videoPending,   setVideoPending]   = useState<Set<string>>(new Set());
  // whether the backend VideoGenerator is ready (checked once on mount)
  const videoEnabledRef = useRef<boolean>(false);

  const {
    session,
    setSession,
    knowledgePayload,
    currentModuleIndex,
    setCurrentModuleIndex,
    wsConnected,
    error,
    setError,
    completeModule,
    student,
    setStudent,
    labView,
    setLabView,
    rehydrate,
  } = useAppStore();

  const currentModule = useAppStore(selectCurrentModule);

  // ── WebSocket ────────────────────────────────────────────────────────────
  const { sendFullPipeline, sendEngagementSignal } = useWebSocket({
    sessionId,
    autoConnect: true,
    onModuleStream: (mod, index, isFirst) => {
      setStreamedModules(prev => {
        const next = [...prev];
        next[index] = mod;
        return next;
      });
      // Mark this module as pending a video only if the backend pipeline is ready
      if (videoEnabledRef.current) {
        setVideoPending(prev => new Set([...prev, mod.module_id]));
      }
      if (isFirst) {
        setCurrentModuleIndex(0);
        setIsLoadingContent(false);
        setLoadingStep('');
        setLabView('learning');
      }
    },
    onKnowledgePayload: () => { /* stored in store by hook */ },
    onUIUpdate: (componentTree) => {
      setUIComponentTree(componentTree);
      setCurrentModuleIndex(0);
      setIsLoadingContent(false);
      setLoadingStep('');
      setLabView('learning');
    },
    onSessionComplete: () => setLabView('complete'),
    onPipelineStatus: (step, status) => {
      if (status === 'processing') {
        const labels: Record<string, string> = {
          biometric_analysis: 'Analysing cognitive state…',
          knowledge_query:    'Generating content…',
          ui_orchestration:   'Building your interface…',
        };
        setLoadingStep(labels[step] ?? 'Processing…');
      }
    },
    onVideoReady: (moduleId, videoUrl) => {
      setModuleVideos(prev => ({ ...prev, [moduleId]: videoUrl }));
      setVideoPending(prev => {
        const next = new Set(prev);
        next.delete(moduleId);
        return next;
      });
    },
    onError: (err) => {
      setError(err.message);
      setIsLoadingContent(false);
      setLoadingStep('');
    },
  });

  // ── Mount effects ────────────────────────────────────────────────────────
  useEffect(() => {
    rehydrate();
    // Check whether the backend video pipeline is ready so we know whether to
    // show "Generating video…" spinners.
    fetch(`${config.backend_url}/health`)
      .then(r => r.json())
      .then(data => {
        videoEnabledRef.current = data?.components?.video_generator === 'ready';
      })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setSession({
      id: sessionId,
      status: 'initializing',
      created_at: new Date().toISOString(),
      current_module_index: 0,
      completed_modules: [],
    });
  }, [sessionId, setSession]);

  // ── Handlers ─────────────────────────────────────────────────────────────
  const handleEnter = useCallback(
    (reg: StudentRegistration) => {
      setStudent(reg);
      setLabView('topic');
    },
    [setStudent, setLabView]
  );

  const handleTopicSubmit = useCallback(
    (query: string) => {
      setError(null);
      setStreamedModules([]);
      setUIComponentTree(null);
      setIsLoadingContent(true);
      void sendFullPipeline(query, [], 0);

      // 120 s timeout — local LLMs can take 30–90 s on first token
      const t = setTimeout(() => {
        setIsLoadingContent(false);
        setStreamedModules(prev => {
          if (prev.length === 0) {
            setError('Request timed out (120 s). Make sure the backend and Ollama are running.');
          }
          return prev;
        });
      }, 120_000);
      return () => clearTimeout(t);
    },
    [sendFullPipeline, setError]
  );

  const handleModuleComplete = useCallback(() => {
    if (currentModule) {
      completeModule(currentModule.module_id);
      sendEngagementSignal('understood');
    }
  }, [currentModule, completeModule, sendEngagementSignal]);

  const handleNeedHelp = useCallback(() => {
    sendEngagementSignal('confused');
    setError('Help requested — adjusting content…');
  }, [sendEngagementSignal, setError]);

  const handleNewTopic = useCallback(() => {
    setUIComponentTree(null);
    setStreamedModules([]);
    setModuleVideos({});
    setVideoPending(new Set());
    setIsLoadingContent(false);
    setError(null);
    setLabView('topic');
  }, [setLabView, setError]);

  const handleLogout = useCallback(() => {
    setStudent(null);
    setUIComponentTree(null);
    setStreamedModules([]);
    setModuleVideos({});
    setVideoPending(new Set());
    setIsLoadingContent(false);
    setError(null);
    setLabView('register');
  }, [setStudent, setLabView, setError]);

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">

        {/* Header */}
        <header className="bg-white shadow-sm sticky top-0 z-10">
          <div className="max-w-5xl mx-auto px-4 py-4 sm:px-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="w-7 h-7 text-blue-600" />
              <div>
                <h1 className="text-lg font-bold text-gray-900 leading-tight">
                  Student Lab — AI Learning Assistant
                </h1>
                <p className="text-xs text-gray-500">Adaptive content powered by AI</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Resources button — visible whenever a student is logged in */}
              {student && labView !== 'register' && (
                <button
                  onClick={() => setLabView(labView === 'resources' ? 'topic' : 'resources')}
                  className={`flex items-center gap-1.5 text-xs font-medium transition-colors ${
                    labView === 'resources'
                      ? 'text-blue-600'
                      : 'text-gray-500 hover:text-blue-600'
                  }`}
                  title="Manage knowledge base resources"
                >
                  <BookMarked className="w-4 h-4" /> Resources
                </button>
              )}
              {student && labView !== 'register' && (
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-red-600 transition-colors"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" /> Sign out
                </button>
              )}
              {wsConnected ? (
                <span className="hidden sm:flex items-center gap-1 text-xs text-green-600">
                  <Wifi className="w-3.5 h-3.5" /> Connected
                </span>
              ) : (
                <span className="hidden sm:flex items-center gap-1 text-xs text-gray-400">
                  <WifiOff className="w-3.5 h-3.5" /> Disconnected
                </span>
              )}
            </div>
          </div>
        </header>

        {/* Main */}
        <main className="max-w-5xl mx-auto px-4 py-10 sm:px-6">

          {/* Global error banner */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1 text-sm text-red-700">{error}</div>
              <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 text-lg leading-none">×</button>
            </div>
          )}

          {/* ── VIEW: Register / Login ── */}
          {labView === 'register' && (
            <RegistrationPanel onEnter={handleEnter} />
          )}

          {/* ── VIEW: Resources ── */}
          {labView === 'resources' && (
            <ResourcesPanel onBack={() => setLabView(student ? 'topic' : 'register')} />
          )}

          {/* ── VIEW: Topic ── */}
          {labView === 'topic' && student && (
            <TopicPanel
              student={student}
              onSubmit={handleTopicSubmit}
              isLoading={isLoadingContent}
              wsConnected={wsConnected}
              loadingStep={loadingStep}
            />
          )}

          {/* ── VIEW: Learning ── */}
          {labView === 'learning' && streamedModules.length > 0 && (() => {
            // Use streamed modules immediately; fall back to knowledgePayload once full
            const modules = knowledgePayload?.teaching_modules ?? streamedModules;
            const activeModule = modules[currentModuleIndex] ?? streamedModules[currentModuleIndex];
            const coreConcept = knowledgePayload?.core_concept
              ?? (streamedModules[0]?.title ?? 'Loading…');
            const isStillStreaming = !knowledgePayload && streamedModules.length > 0;

            return (
              <div>
                {/* Session info bar */}
                <div className="bg-white rounded-xl shadow-sm p-4 mb-6 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs text-gray-500">Learning session for</p>
                    <p className="font-semibold text-gray-900 text-sm">
                      {student?.fullName} &middot; {coreConcept}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {isStillStreaming && (
                      <span className="flex items-center gap-1.5 text-xs text-blue-600 animate-pulse">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-ping" />
                        Generating more…
                      </span>
                    )}
                    <button onClick={handleNewTopic} className="text-xs text-blue-600 hover:underline">
                      ← New topic
                    </button>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
                  <div className="flex justify-between text-xs text-gray-500 mb-1.5">
                    <span className="font-medium text-gray-700">Progress</span>
                    <span>
                      {currentModuleIndex + 1} / {modules.length} modules
                      {isStillStreaming && ' (more loading…)'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${((currentModuleIndex + 1) / Math.max(modules.length, 1)) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Module cards — render streamed modules directly when uiComponentTree isn't ready */}
                {uiComponentTree ? (
                  <div className="bg-white rounded-2xl shadow-lg p-6">
                    <DynamicUIRenderer
                      componentTree={uiComponentTree}
                      currentModule={activeModule || undefined}
                      cognitiveLoad={undefined}
                      onModuleComplete={handleModuleComplete}
                      onNeedHelp={handleNeedHelp}
                    />
                  </div>
                ) : (
                  <div className="space-y-4">
                    {streamedModules.map((mod, i) => (
                      <div
                        key={mod.module_id}
                        className={`bg-white rounded-2xl shadow-lg p-6 border-2 transition-all ${
                          i === currentModuleIndex ? 'border-blue-400' : 'border-transparent'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            mod.type === 'explanation' ? 'bg-blue-100 text-blue-700' :
                            mod.type === 'code_example' ? 'bg-purple-100 text-purple-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {mod.type.replace('_', ' ')}
                          </span>
                          <span className="text-xs text-gray-400">{mod.estimated_time}s</span>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">{mod.title}</h3>
                        <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{mod.content}</p>
                        {/* Video player — shown once backend sends video_ready */}
                        {moduleVideos[mod.module_id] ? (
                          <VideoPlayer
                            videoUrl={moduleVideos[mod.module_id]}
                            moduleTitle={mod.title}
                          />
                        ) : videoPending.has(mod.module_id) && (
                          <div className="mt-4 flex items-center gap-2 text-xs text-gray-400">
                            <span className="w-3.5 h-3.5 border-2 border-gray-300 border-t-blue-400 rounded-full animate-spin flex-shrink-0" />
                            Generating video…
                          </div>
                        )}
                      </div>
                    ))}

                    {isStillStreaming && (
                      <div className="bg-white rounded-2xl shadow-sm p-6 border-2 border-dashed border-blue-200 text-center text-blue-400 text-sm animate-pulse">
                        Generating next module…
                      </div>
                    )}

                    {/* Module navigation */}
                    <div className="bg-white rounded-xl shadow-sm p-4 flex gap-3">
                      <button
                        onClick={handleModuleComplete}
                        disabled={currentModuleIndex >= modules.length - 1}
                        className="flex-1 py-2.5 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 transition-colors text-sm"
                      >
                        {currentModuleIndex >= modules.length - 1 ? '✓ Done' : 'Next module →'}
                      </button>
                      <button
                        onClick={handleNeedHelp}
                        className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors text-sm"
                      >
                        Need Help
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })()}

          {/* ── VIEW: Complete ── */}
          {labView === 'complete' && (
            <div className="max-w-lg mx-auto bg-white rounded-2xl shadow-lg p-10 text-center">
              <CheckCircle className="w-14 h-14 text-green-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Session Complete!</h2>
              <p className="text-gray-500 text-sm mb-6">
                Great work, <strong>{student?.fullName}</strong>. You've finished the learning
                session on <strong>{knowledgePayload?.core_concept}</strong>.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={handleNewTopic}
                  className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors text-sm"
                >
                  Start a new topic
                </button>
                <button
                  onClick={handleLogout}
                  className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors text-sm"
                >
                  Sign out
                </button>
              </div>
            </div>
          )}

          {/* Debug panel (dev only) */}
          {config.debug_mode && (
            <div className="mt-8 bg-gray-900 text-gray-100 rounded-xl p-4 text-xs font-mono">
              <div className="font-bold mb-2 text-gray-400">Debug</div>
              <div>Session: {sessionId}</div>
              <div>View: {labView}</div>
              <div>Student: {student?.studentId ?? 'none'}</div>
              <div>Status: {session?.status}</div>
              <div>WS: {wsConnected ? 'connected' : 'disconnected'}</div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-16">
          <div className="max-w-5xl mx-auto px-4 py-5 text-center">
            <p className="text-xs text-gray-400">
              Ephemeral Intent Synthesis System &mdash; AI-Powered Student Lab Assistant
            </p>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
}

export default App;
