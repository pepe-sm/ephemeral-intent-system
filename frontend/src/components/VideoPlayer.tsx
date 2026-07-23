/**
 * VideoPlayer
 * Displays a generated talking-head video for a teaching module.
 * Renders nothing when no video URL is available (graceful degradation).
 */

import React, { useRef, useState } from 'react';
import { Play, Pause, Volume2, VolumeX, Video } from 'lucide-react';

interface Props {
  /** URL returned by the backend video_ready message, e.g. /api/v1/video/abc123.mp4 */
  videoUrl: string;
  /** Human-readable label shown above the player */
  moduleTitle?: string;
}

export function VideoPlayer({ videoUrl, moduleTitle }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [error, setError] = useState(false);

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

  if (error) {
    return (
      <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700 flex items-center gap-2">
        <Video className="w-4 h-4 flex-shrink-0" />
        Video unavailable — showing text content only.
      </div>
    );
  }

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
        onEnded={() => setPlaying(false)}
        onError={() => setError(true)}
        onClick={toggle}
        title="Click to play / pause"
      />
    </div>
  );
}

// Made with Bob
