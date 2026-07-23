/**
 * TopicPanel
 * Shown after login — lets the student enter a query to generate learning content.
 */

import React, { useState } from 'react';
import { BookOpen, Wifi, WifiOff, AlertCircle } from 'lucide-react';
import type { StudentRegistration } from '@/types';

interface Props {
  student: StudentRegistration;
  onSubmit: (query: string) => void;
  isLoading: boolean;
  wsConnected: boolean;
  loadingStep: string;
}

export function TopicPanel({ student, onSubmit, isLoading, wsConnected, loadingStep }: Props) {
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
            <span className="text-blue-600 font-bold text-sm">
              {student.fullName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
            </span>
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

      {/* Query form */}
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

// Made with Bob
