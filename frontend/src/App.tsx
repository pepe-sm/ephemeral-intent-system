/**
 * Main App Component — Student Lab Registration Flow
 * Ephemeral Intent Synthesis System
 *
 * Flow: Register → Pick Topic → Learning Session → Complete
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { DynamicUIRenderer } from '@/components/DynamicUI/DynamicUIRenderer';
import { useAppStore, selectCurrentModule } from '@/store/appStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { config } from '@/config';
import type { UIComponentTree, StudentRegistration } from '@/types';
import { Brain, Wifi, WifiOff, AlertCircle, BookOpen, CheckCircle, User, LogOut } from 'lucide-react';

// Predefined lab courses for the registration form
const LAB_COURSES = [
  'Introduction to Programming',
  'Data Structures & Algorithms',
  'Web Development',
  'Database Systems',
  'Computer Networks',
  'Operating Systems',
  'Software Engineering',
  'Artificial Intelligence',
  'Machine Learning',
  'Cybersecurity',
];

const LAB_GROUPS = ['Group A', 'Group B', 'Group C', 'Group D', 'Group E', 'Group F'];

// ────────────────────────────────────────────────────────────────────────────
// Registration Panel
// ────────────────────────────────────────────────────────────────────────────
function RegistrationPanel({
  onRegister,
}: {
  onRegister: (s: StudentRegistration) => void;
}) {
  const [form, setForm] = useState({
    studentId: '',
    fullName: '',
    labGroup: LAB_GROUPS[0],
    course: LAB_COURSES[0],
  });
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.studentId.trim()) { setError('Student ID is required.'); return; }
    if (!form.fullName.trim()) { setError('Full name is required.'); return; }
    setError('');
    onRegister({ ...form, registeredAt: new Date().toISOString() });
  };

  return (
    <div className="max-w-lg mx-auto bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center gap-3 mb-6">
        <User className="w-6 h-6 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900">Student Lab Registration</h2>
      </div>
      <p className="text-gray-500 mb-6 text-sm">
        Register to start your personalised learning session. No camera required.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Student ID *</label>
          <input
            type="text"
            value={form.studentId}
            onChange={e => setForm(f => ({ ...f, studentId: e.target.value }))}
            placeholder="e.g. s12345678"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
          <input
            type="text"
            value={form.fullName}
            onChange={e => setForm(f => ({ ...f, fullName: e.target.value }))}
            placeholder="e.g. Jane Smith"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lab Group</label>
            <select
              value={form.labGroup}
              onChange={e => setForm(f => ({ ...f, labGroup: e.target.value }))}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white"
            >
              {LAB_GROUPS.map(g => <option key={g}>{g}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Course</label>
            <select
              value={form.course}
              onChange={e => setForm(f => ({ ...f, course: e.target.value }))}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white"
            >
              {LAB_COURSES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <button
          type="submit"
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors text-sm mt-2"
        >
          Register &amp; Start Lab
        </button>
      </form>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Topic Selection Panel
// ────────────────────────────────────────────────────────────────────────────
function TopicPanel({
  student,
  onSubmit,
  isLoading,
  wsConnected,
  loadingStep,
}: {
  student: StudentRegistration;
  onSubmit: (query: string) => void;
  isLoading: boolean;
  wsConnected: boolean;
  loadingStep: string;
}) {
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) { setError('Please enter a topic or question.'); return; }
    setError('');
    onSubmit(query.trim());
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Student badge */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <User className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900 text-sm">{student.fullName}</p>
            <p className="text-xs text-gray-500">{student.studentId} · {student.labGroup} · {student.course}</p>
          </div>
        </div>
        {wsConnected ? (
          <span className="flex items-center gap-1.5 text-xs text-green-600 font-medium">
            <Wifi className="w-4 h-4" /> Live
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-xs text-amber-600 font-medium">
            <WifiOff className="w-4 h-4" /> Connecting…
          </span>
        )}
      </div>

      {/* Topic form */}
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="flex items-center gap-3 mb-2">
          <BookOpen className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-bold text-gray-900">What would you like to learn?</h2>
        </div>
        <p className="text-gray-500 text-sm mb-6">
          Enter any topic, concept, or question from your <strong>{student.course}</strong> course.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={`e.g. "Explain binary search trees" or "How does TCP handshake work?"`}
            rows={3}
            disabled={isLoading}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                {loadingStep || 'Generating learning content…'}
              </span>
            ) : (
              'Generate Learning Content'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Main App
// ────────────────────────────────────────────────────────────────────────────
function App() {
  const [sessionId] = useState(
    () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );
  const [uiComponentTree, setUIComponentTree] = useState<UIComponentTree | null>(null);
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');

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
  } = useAppStore();

  const currentModule = useAppStore(selectCurrentModule);

  // WebSocket
  const { sendFullPipeline, sendEngagementSignal } = useWebSocket({
    sessionId,
    autoConnect: true,
    onKnowledgePayload: () => {
      // knowledge stored in appStore by the hook; wait for UI update
    },
    onUIUpdate: (componentTree) => {
      setUIComponentTree(componentTree);
      setCurrentModuleIndex(0);
      setIsLoadingContent(false);
      setLoadingStep('');
      setLabView('learning');
    },
    onSessionComplete: () => {
      setLabView('complete');
    },
    onError: (err) => {
      setError(err.message);
      setIsLoadingContent(false);
      setLoadingStep('');
    },
  });

  // Initialise session on mount
  useEffect(() => {
    setSession({
      id: sessionId,
      status: 'initializing',
      created_at: new Date().toISOString(),
      current_module_index: 0,
      completed_modules: [],
    });
  }, [sessionId, setSession]);

  // ── handlers ──

  const handleRegister = useCallback(
    (reg: StudentRegistration) => {
      setStudent(reg);
      setLabView('topic');
    },
    [setStudent, setLabView]
  );

  const handleTopicSubmit = useCallback(
    (query: string) => {
      setError(null);
      setIsLoadingContent(true);
      // sendFullPipeline auto-reconnects if the socket is closed
      void sendFullPipeline(query, [], 0);

      // Allow up to 120 s — local LLMs can take 30-90 s on first token
      const t = setTimeout(() => {
        setIsLoadingContent(false);
        if (!uiComponentTree) {
          setError('Request timed out (120 s). Make sure the backend and Ollama are both running.');
        }
      }, 120_000);
      return () => clearTimeout(t);
    },
    [sendFullPipeline, setError, uiComponentTree]
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
    setIsLoadingContent(false);
    setError(null);
    setLabView('topic');
  }, [setLabView, setError]);

  const handleLogout = useCallback(() => {
    setStudent(null);
    setUIComponentTree(null);
    setIsLoadingContent(false);
    setError(null);
    setLabView('register');
  }, [setStudent, setLabView, setError]);

  // ── render ──

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
              {student && labView !== 'register' && (
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-red-600 transition-colors"
                  title="Log out"
                >
                  <LogOut className="w-4 h-4" />
                  Sign out
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

          {/* ── VIEW: Register ── */}
          {labView === 'register' && (
            <RegistrationPanel onRegister={handleRegister} />
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
          {labView === 'learning' && knowledgePayload && uiComponentTree && (
            <div>
              {/* Session info bar */}
              <div className="bg-white rounded-xl shadow-sm p-4 mb-6 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs text-gray-500">Learning session for</p>
                  <p className="font-semibold text-gray-900 text-sm">
                    {student?.fullName} &middot; {knowledgePayload.core_concept}
                  </p>
                </div>
                <button
                  onClick={handleNewTopic}
                  className="text-xs text-blue-600 hover:underline"
                >
                  ← New topic
                </button>
              </div>

              {/* Progress bar */}
              <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
                <div className="flex justify-between text-xs text-gray-500 mb-1.5">
                  <span className="font-medium text-gray-700">Progress</span>
                  <span>{currentModuleIndex + 1} / {knowledgePayload.teaching_modules.length} modules</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${((currentModuleIndex + 1) / knowledgePayload.teaching_modules.length) * 100}%`,
                    }}
                  />
                </div>
              </div>

              {/* Dynamic content */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <DynamicUIRenderer
                  componentTree={uiComponentTree}
                  currentModule={currentModule || undefined}
                  cognitiveLoad={undefined}
                  onModuleComplete={handleModuleComplete}
                  onNeedHelp={handleNeedHelp}
                />
              </div>
            </div>
          )}

          {/* ── VIEW: Complete ── */}
          {labView === 'complete' && (
            <div className="max-w-lg mx-auto bg-white rounded-2xl shadow-lg p-10 text-center">
              <CheckCircle className="w-14 h-14 text-green-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Session Complete!</h2>
              <p className="text-gray-500 text-sm mb-6">
                Great work, <strong>{student?.fullName}</strong>. You've finished the learning session
                on <strong>{knowledgePayload?.core_concept}</strong>.
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

// Made with Bob for IBM AI Builders Challenge
