/**
 * VideoPlayer
 * Displays a generated talking-head video for a teaching module.
 * Renders nothing when no video URL is available (graceful degradation).
 * Includes a timeline scrubber, current-time/duration display, and mute toggle.
 */

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Play, Pause, Volume2, VolumeX, Video } from 'lucide-react';

interface Props {
  /** URL returned by the backend video_ready message, e.g. /api/v1/video/abc123.mp4 */
  videoUrl: string;
  /** Human-readable label shown above the player */
  moduleTitle?: string;
}

function fmt(sec: number): string {
  if (!isFinite(sec) || sec < 0) return '0:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function VideoPlayer({ videoUrl, moduleTitle }: Props) {
  const videoRef    = useRef<HTMLVideoElement>(null);
  const scrubRef    = useRef<HTMLInputElement>(null);
  const [playing,   setPlaying]   = useState(false);
  const [muted,     setMuted]     = useState(false);
  const [current,   setCurrent]   = useState(0);
  const [duration,  setDuration]  = useState(0);
  const [error,     setError]     = useState(false);

  // Keep scrubber in sync with video playback
  const onTimeUpdate = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    setCurrent(v.currentTime);
    if (scrubRef.current) scrubRef.current.value = String(v.currentTime);
  }, []);

  const onLoadedMetadata = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    setDuration(v.duration);
    if (scrubRef.current) {
      scrubRef.current.max = String(v.duration);
    }
  }, []);

  // Sync scrubber max whenever duration changes
  useEffect(() => {
    if (scrubRef.current && duration > 0) scrubRef.current.max = String(duration);
  }, [duration]);

  const toggle = () => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) {
      v.play().then(() => setPlaying(true)).catch(() => setError(true));
    } else {
      v.pause();
      setPlaying(false);
    }
  };

  const toggleMute = () => {
    const v = videoRef.current;
    if (!v) return;
    v.muted = !v.muted;
    setMuted(v.muted);
  };

  const handleScrub = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = videoRef.current;
    if (!v) return;
    const t = parseFloat(e.target.value);
    v.currentTime = t;
    setCurrent(t);
  };

  if (error) {
    return (
      <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700 flex items-center gap-2">
        <Video className="w-4 h-4 flex-shrink-0" />
        Video unavailable — showing text content only.
      </div>
    );
  }

  const progress = duration > 0 ? (current / duration) * 100 : 0;

  return (
    <div className="mt-4 rounded-xl overflow-hidden border border-gray-200 bg-black">
      {/* Label bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-gray-900">
        <div className="flex items-center gap-1.5 text-xs text-gray-400">
          <Video className="w-3.5 h-3.5 text-blue-400" />
          <span className="truncate max-w-[220px]">
            {moduleTitle ? `Video: ${moduleTitle}` : 'AI-generated video'}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={toggleMute}
            className="p-1 text-gray-400 hover:text-white transition-colors"
            title={muted ? 'Unmute' : 'Mute'}
          >
            {muted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={toggle}
            className="p-1 text-gray-400 hover:text-white transition-colors"
            title={playing ? 'Pause' : 'Play'}
          >
            {playing ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Video element */}
      <video
        ref={videoRef}
        src={videoUrl}
        className="w-full max-h-56 object-contain bg-black cursor-pointer"
        playsInline
        onTimeUpdate={onTimeUpdate}
        onLoadedMetadata={onLoadedMetadata}
        onEnded={() => setPlaying(false)}
        onError={() => setError(true)}
        onClick={toggle}
        title="Click to play / pause"
      />

      {/* Controls bar */}
      <div className="bg-gray-900 px-3 py-1.5 flex items-center gap-2">
        {/* time */}
        <span className="text-[10px] text-gray-400 font-mono tabular-nums min-w-[60px]">
          {fmt(current)} / {fmt(duration)}
        </span>

        {/* scrubber */}
        <div className="relative flex-1 h-2 group">
          {/* filled track */}
          <div
            className="absolute inset-y-0 left-0 bg-blue-500 rounded-full pointer-events-none"
            style={{ width: `${progress}%` }}
          />
          {/* background track */}
          <div className="absolute inset-0 bg-gray-700 rounded-full pointer-events-none" style={{ zIndex: -1 }} />
          <input
            ref={scrubRef}
            type="range"
            min="0"
            step="0.1"
            defaultValue="0"
            onChange={handleScrub}
            className="absolute inset-0 w-full opacity-0 cursor-pointer h-2"
            aria-label="Video timeline"
          />
        </div>
      </div>
    </div>
  );
}

// Made with Bob
