/**
 * ResourcesPanel
 * Lets users add documents (text paste, file upload, or URL fetch) to the
 * RAG knowledge base, and view / delete resources already indexed.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  BookMarked, Upload, Trash2, FileText, Link, Globe,
  AlertCircle, CheckCircle, RefreshCw, X,
} from 'lucide-react';
import type { Resource } from '@/types';
import { config } from '@/config';

interface Props {
  onBack: () => void;
}

type IngestMode = 'text' | 'file' | 'url';
type Status =
  | { type: 'idle' }
  | { type: 'loading' }
  | { type: 'success'; msg: string }
  | { type: 'error'; msg: string };

const CONTENT_TYPE_COLORS: Record<string, string> = {
  text:  'bg-blue-100 text-blue-700',
  md:    'bg-indigo-100 text-indigo-700',
  pdf:   'bg-red-100 text-red-700',
  url:   'bg-green-100 text-green-700',
};

function ctBadge(ct: string) {
  const cls = CONTENT_TYPE_COLORS[ct] ?? 'bg-gray-100 text-gray-600';
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${cls}`}>
      {ct.toUpperCase()}
    </span>
  );
}

function fmtDate(iso?: string) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return '';
  }
}

async function apiFetch(path: string, init?: RequestInit) {
  const res = await fetch(`${config.backend_url}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export function ResourcesPanel({ onBack }: Props) {
  const [mode, setMode] = useState<IngestMode>('text');
  const [title, setTitle] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [urlInput, setUrlInput] = useState('');
  const [status, setStatus] = useState<Status>({ type: 'idle' });
  const [resources, setResources] = useState<Resource[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Load existing resources on mount ────────────────────────────────────
  const fetchResources = async () => {
    setLoadingList(true);
    try {
      const data = await apiFetch('/api/v1/resources');
      setResources(data.resources ?? []);
    } catch {
      setResources([]);
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => { void fetchResources(); }, []);

  // ── Submit handler ───────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) { setStatus({ type: 'error', msg: 'Title is required.' }); return; }
    if (mode === 'text' && !text.trim()) { setStatus({ type: 'error', msg: 'Paste some text to ingest.' }); return; }
    if (mode === 'file' && !file) { setStatus({ type: 'error', msg: 'Select a file to upload.' }); return; }
    if (mode === 'url' && !urlInput.trim()) { setStatus({ type: 'error', msg: 'Enter a URL to fetch.' }); return; }

    setStatus({ type: 'loading' });

    try {
      let result: Record<string, unknown>;

      if (mode === 'url') {
        const fd = new FormData();
        fd.append('title', title.trim());
        fd.append('url', urlInput.trim());
        result = await apiFetch('/api/v1/resources/ingest-url', { method: 'POST', body: fd });
      } else {
        const fd = new FormData();
        fd.append('title', title.trim());
        if (sourceUrl.trim()) fd.append('source_url', sourceUrl.trim());
        if (mode === 'text') fd.append('text', text.trim());
        if (mode === 'file' && file) fd.append('file', file);
        result = await apiFetch('/api/v1/resources/ingest', { method: 'POST', body: fd });
      }

      const chunks = result.chunks_added as number;
      const chars  = result.characters_extracted as number | undefined;
      let msg = `✓ "${result.title}" indexed — ${chunks} chunk${chunks !== 1 ? 's' : ''} added.`;
      if (chars !== undefined) msg += ` (${chars.toLocaleString()} chars extracted)`;
      setStatus({ type: 'success', msg });

      // Reset form fields
      setTitle(''); setSourceUrl(''); setText(''); setFile(null); setUrlInput('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      void fetchResources();
    } catch (err) {
      setStatus({ type: 'error', msg: err instanceof Error ? err.message : 'Ingestion failed.' });
    }
  };

  // ── Delete handler ───────────────────────────────────────────────────────
  const handleDelete = async (id: string, resourceTitle: string) => {
    if (!window.confirm(`Remove "${resourceTitle}" from the knowledge base?`)) return;
    try {
      await apiFetch(`/api/v1/resources/${id}`, { method: 'DELETE' });
      setResources(prev => prev.filter(r => r.id !== id));
    } catch (err) {
      setStatus({ type: 'error', msg: err instanceof Error ? err.message : 'Delete failed.' });
    }
  };

  // ── Drag-and-drop ────────────────────────────────────────────────────────
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) { setFile(dropped); setMode('file'); }
  };

  // ── Mode tab config ──────────────────────────────────────────────────────
  const modes: { id: IngestMode; label: string; Icon: React.FC<{ className?: string }> }[] = [
    { id: 'text', label: 'Paste text', Icon: FileText },
    { id: 'file', label: 'Upload file', Icon: Upload },
    { id: 'url',  label: 'From URL',   Icon: Globe },
  ];

  return (
    <div className="max-w-3xl mx-auto">

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BookMarked className="w-6 h-6 text-blue-600" />
          <div>
            <h2 className="font-bold text-gray-900 text-lg leading-tight">Knowledge Base</h2>
            <p className="text-xs text-gray-500">Add resources to improve RAG retrieval quality</p>
          </div>
        </div>
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-800 transition-colors"
        >
          <X className="w-4 h-4" /> Close
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* ── Ingest form (left / top) ── */}
        <div className="lg:col-span-3 bg-white rounded-2xl shadow-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-4 text-sm uppercase tracking-wide">Add Resource</h3>

          {/* Mode toggle */}
          <div className="flex gap-2 mb-4">
            {modes.map(({ id, label, Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setMode(id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  mode === id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>

          {/* Status banner */}
          {status.type !== 'idle' && (
            <div className={`mb-4 p-3 rounded-lg text-sm flex items-start gap-2 ${
              status.type === 'success' ? 'bg-green-50 border border-green-200 text-green-700'
              : status.type === 'error' ? 'bg-red-50 border border-red-200 text-red-700'
              : 'bg-blue-50 border border-blue-200 text-blue-700'
            }`}>
              {status.type === 'success' && <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />}
              {status.type === 'error' && <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />}
              {status.type === 'loading' && (
                <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin flex-shrink-0 mt-0.5" />
              )}
              <span>{status.type === 'loading' ? 'Indexing resource…' : status.msg}</span>
              {status.type !== 'loading' && (
                <button onClick={() => setStatus({ type: 'idle' })} className="ml-auto opacity-60 hover:opacity-100">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Title */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder={
                  mode === 'url'
                    ? 'e.g. Python Docs — asyncio'
                    : 'e.g. Lecture 3 — Binary Trees'
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* URL input (url mode) */}
            {mode === 'url' && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  <span className="flex items-center gap-1">
                    <Globe className="w-3 h-3" /> Web page URL <span className="text-red-500">*</span>
                  </span>
                </label>
                <input
                  type="url"
                  value={urlInput}
                  onChange={e => setUrlInput(e.target.value)}
                  placeholder="https://docs.python.org/…"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-400 mt-1">
                  The page will be fetched server-side and its text extracted automatically.
                </p>
              </div>
            )}

            {/* Source URL (text / file modes) */}
            {mode !== 'url' && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  <span className="flex items-center gap-1">
                    <Link className="w-3 h-3" /> Source URL{' '}
                    <span className="text-gray-400 font-normal">(optional)</span>
                  </span>
                </label>
                <input
                  type="url"
                  value={sourceUrl}
                  onChange={e => setSourceUrl(e.target.value)}
                  placeholder="https://…"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            )}

            {/* Text area */}
            {mode === 'text' && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Content <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={text}
                  onChange={e => setText(e.target.value)}
                  placeholder="Paste lecture notes, documentation, textbook excerpts…"
                  rows={7}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y font-mono"
                />
                <p className="text-xs text-gray-400 mt-1">{text.length.toLocaleString()} characters</p>
              </div>
            )}

            {/* File upload */}
            {mode === 'file' && (
              <div
                onDrop={handleDrop}
                onDragOver={e => e.preventDefault()}
                className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors"
              >
                {file ? (
                  <div className="flex items-center justify-center gap-2 text-sm text-gray-700">
                    <FileText className="w-4 h-4 text-blue-500" />
                    <span className="font-medium">{file.name}</span>
                    <span className="text-gray-400">({(file.size / 1024).toFixed(1)} KB)</span>
                    <button
                      type="button"
                      onClick={() => setFile(null)}
                      className="text-red-400 hover:text-red-600 ml-1"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">Drag & drop a file here, or</p>
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="mt-1 text-sm text-blue-600 hover:underline font-medium"
                    >
                      browse to select
                    </button>
                    <p className="text-xs text-gray-400 mt-1">Supports .txt · .md · .pdf</p>
                  </>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.md,.pdf"
                  className="hidden"
                  onChange={e => setFile(e.target.files?.[0] ?? null)}
                />
              </div>
            )}

            <button
              type="submit"
              disabled={status.type === 'loading'}
              className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm"
            >
              {status.type === 'loading' ? 'Indexing…' : 'Add to Knowledge Base'}
            </button>
          </form>
        </div>

        {/* ── Indexed resources list (right / bottom) ── */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 text-sm uppercase tracking-wide">
              Indexed Resources
              {resources.length > 0 && (
                <span className="ml-2 text-xs font-normal text-gray-400">({resources.length})</span>
              )}
            </h3>
            <button
              onClick={fetchResources}
              disabled={loadingList}
              className="text-gray-400 hover:text-gray-700 transition-colors"
              title="Refresh list"
            >
              <RefreshCw className={`w-4 h-4 ${loadingList ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {loadingList && resources.length === 0 && (
            <div className="flex items-center justify-center py-8 text-gray-400 text-sm gap-2">
              <span className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
              Loading…
            </div>
          )}

          {!loadingList && resources.length === 0 && (
            <div className="text-center py-8 text-gray-400">
              <BookMarked className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No resources indexed yet.</p>
              <p className="text-xs mt-1">Add your first resource on the left.</p>
            </div>
          )}

          <ul className="space-y-2">
            {resources.map(r => (
              <li key={r.id} className="flex items-start gap-2 p-2.5 rounded-lg hover:bg-gray-50 group">
                <FileText className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <p className="text-sm font-medium text-gray-800 truncate">{r.title}</p>
                    {ctBadge(r.content_type)}
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {r.chunk_count} chunk{r.chunk_count !== 1 ? 's' : ''}
                    {r.ingested_at && (
                      <span className="ml-1 text-gray-300">· {fmtDate(r.ingested_at)}</span>
                    )}
                  </p>
                  {r.source_url && (
                    <a
                      href={r.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-500 hover:underline truncate block"
                    >
                      {r.source_url}
                    </a>
                  )}
                </div>
                <button
                  onClick={() => handleDelete(r.id, r.title)}
                  className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all flex-shrink-0 mt-0.5"
                  title="Remove from knowledge base"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

// Made with Bob
