/**
 * VideoLibrary
 * Browses all locally-generated MP4 files served by /api/v1/video/
 * Works regardless of whether VIDEO_ENABLED is set — the files already
 * exist on disk, this just makes them accessible.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { VideoPlayer } from '@/components/VideoPlayer';
import { config } from '@/config';
import { Film, RefreshCw, AlertCircle } from 'lucide-react';

interface VideoEntry {
  filename: string;
  url: string;
  size_bytes: number;
  created_at: string;
}

interface Props {
  onBack: () => void;
}

function fmtBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fmtDate(iso: string): string {
  try {
    return new Date(iso + 'Z').toLocaleString();
  } catch {
    return iso;
  }
}

export function VideoLibrary({ onBack }: Props) {
  const [videos,    setVideos]    = useState<VideoEntry[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState<string | null>(null);
  const [expanded,  setExpanded]  = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res  = await fetch(`${config.backend_url}/api/v1/video/`);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      setVideos(data.videos ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not reach backend');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Film className="w-5 h-5 text-indigo-600" />
          <h2 className="text-xl font-bold text-gray-900">Generated Videos</h2>
          {!loading && (
            <span className="ml-1 text-xs text-gray-400 font-normal">
              {videos.length} file{videos.length !== 1 ? 's' : ''} on disk
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-indigo-600 transition-colors disabled:opacity-50"
            title="Refresh list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={onBack}
            className="text-xs text-blue-600 hover:underline"
          >
            ← Back
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && !error && (
        <div className="text-center py-12 text-gray-400 text-sm">Loading…</div>
      )}

      {/* Empty */}
      {!loading && !error && videos.length === 0 && (
        <div className="text-center py-12 text-gray-400 text-sm">
          No videos found. Run a learning session to generate videos.
        </div>
      )}

      {/* Video list */}
      {!loading && videos.length > 0 && (
        <div className="space-y-3">
          {videos.map((v) => (
            <div
              key={v.filename}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              {/* Row */}
              <button
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                onClick={() => setExpanded(expanded === v.filename ? null : v.filename)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <Film className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{v.filename}</p>
                    <p className="text-xs text-gray-400">{fmtBytes(v.size_bytes)} · {fmtDate(v.created_at)}</p>
                  </div>
                </div>
                <span className="text-xs text-gray-400 ml-3 flex-shrink-0">
                  {expanded === v.filename ? '▲ hide' : '▼ play'}
                </span>
              </button>

              {/* Inline player */}
              {expanded === v.filename && (
                <div className="px-4 pb-4">
                  <VideoPlayer
                    videoUrl={v.url}
                    moduleTitle={v.filename.replace('.mp4', '')}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Made with Bob
