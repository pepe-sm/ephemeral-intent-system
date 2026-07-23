/**
 * RegistrationPanel
 * Handles both new student registration and returning student login.
 * Persists registered students in localStorage so the same ID can log back in.
 */

import React, { useState } from 'react';
import { User, AlertCircle, LogIn, UserPlus } from 'lucide-react';
import type { StudentRegistration } from '@/types';

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

// ---------------------------------------------------------------------------
// Persistence helpers
// ---------------------------------------------------------------------------

const STORAGE_KEY = 'ephemeral_students';

function loadStudents(): Record<string, StudentRegistration> {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}');
  } catch {
    return {};
  }
}

function saveStudent(s: StudentRegistration): void {
  const all = loadStudents();
  all[s.studentId.toLowerCase()] = s;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
}

function findStudent(id: string): StudentRegistration | null {
  return loadStudents()[id.toLowerCase()] ?? null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface Props {
  onEnter: (s: StudentRegistration) => void;
}

export function RegistrationPanel({ onEnter }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [error, setError] = useState('');

  // ── Login state ────────────────────────────────────────────────────────
  const [loginId, setLoginId] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    const id = loginId.trim();
    if (!id) { setError('Please enter your Student ID.'); return; }
    const student = findStudent(id);
    if (!student) {
      setError('Student ID not found. Please register first.');
      return;
    }
    setError('');
    onEnter(student);
  };

  // ── Register state ─────────────────────────────────────────────────────
  const [form, setForm] = useState({
    studentId: '',
    fullName: '',
    labGroup: LAB_GROUPS[0],
    course: LAB_COURSES[0],
  });

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.studentId.trim()) { setError('Student ID is required.'); return; }
    if (!form.fullName.trim()) { setError('Full name is required.'); return; }
    if (findStudent(form.studentId)) {
      setError('This Student ID is already registered. Please log in instead.');
      return;
    }
    const student: StudentRegistration = { ...form, registeredAt: new Date().toISOString() };
    saveStudent(student);
    setError('');
    onEnter(student);
  };

  return (
    <div className="max-w-lg mx-auto bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center gap-3 mb-6">
        <User className="w-6 h-6 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900">Student Lab Portal</h2>
      </div>

      {/* Tab switcher */}
      <div className="flex rounded-lg border border-gray-200 mb-6 overflow-hidden">
        <button
          type="button"
          onClick={() => { setMode('login'); setError(''); }}
          className={`flex-1 py-2.5 text-sm font-medium flex items-center justify-center gap-1.5 transition-colors
            ${mode === 'login' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}
        >
          <LogIn className="w-4 h-4" /> Sign In
        </button>
        <button
          type="button"
          onClick={() => { setMode('register'); setError(''); }}
          className={`flex-1 py-2.5 text-sm font-medium flex items-center justify-center gap-1.5 transition-colors
            ${mode === 'register' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}
        >
          <UserPlus className="w-4 h-4" /> Register
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* ── Login form ── */}
      {mode === 'login' && (
        <form onSubmit={handleLogin} className="space-y-4">
          <p className="text-sm text-gray-500">Enter your Student ID to resume your sessions.</p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Student ID</label>
            <input
              type="text"
              value={loginId}
              onChange={e => setLoginId(e.target.value)}
              placeholder="e.g. s12345678"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              autoFocus
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors text-sm"
          >
            Sign In
          </button>
          <p className="text-center text-xs text-gray-400">
            New student?{' '}
            <button type="button" onClick={() => { setMode('register'); setError(''); }}
              className="text-blue-600 hover:underline">Register here</button>
          </p>
        </form>
      )}

      {/* ── Register form ── */}
      {mode === 'register' && (
        <form onSubmit={handleRegister} className="space-y-4">
          <p className="text-sm text-gray-500">Create your student account to get started.</p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Student ID *</label>
            <input
              type="text"
              value={form.studentId}
              onChange={e => setForm(f => ({ ...f, studentId: e.target.value }))}
              placeholder="e.g. s12345678"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              autoFocus
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
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm bg-white"
              >
                {LAB_GROUPS.map(g => <option key={g}>{g}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Course</label>
              <select
                value={form.course}
                onChange={e => setForm(f => ({ ...f, course: e.target.value }))}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm bg-white"
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
          <p className="text-center text-xs text-gray-400">
            Already registered?{' '}
            <button type="button" onClick={() => { setMode('login'); setError(''); }}
              className="text-blue-600 hover:underline">Sign in</button>
          </p>
        </form>
      )}
    </div>
  );
}

// Made with Bob
