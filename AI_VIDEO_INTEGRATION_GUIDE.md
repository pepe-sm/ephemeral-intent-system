# AI Video Generation Integration Guide

## Overview
This guide explains how to integrate AI-generated video illustrations into the Ephemeral Intent System to enhance the learning experience with visual content.

## 🎯 Goal
Generate educational videos dynamically based on the learning content and user's cognitive state.

---

## 🎬 AI Video Generation Options

### Option 1: D-ID (Recommended for POC)
**Best for:** Talking head videos with AI avatars

- **Pricing:** $5.90/month (Lite) - 20 minutes of video
- **API:** REST API, easy integration
- **Features:**
  - 100+ realistic AI avatars
  - Text-to-video in minutes
  - Multiple languages
  - Custom voices
- **Use Case:** Instructor-style explanations

**Website:** https://www.d-id.com/

### Option 2: Synthesia
**Best for:** Professional training videos

- **Pricing:** $22/month (Personal) - 10 minutes/month
- **API:** Available on Enterprise plan
- **Features:**
  - 140+ AI avatars
  - 120+ languages
  - Screen recordings
  - Custom avatars
- **Use Case:** Polished educational content

**Website:** https://www.synthesia.io/

### Option 3: HeyGen
**Best for:** Quick video creation

- **Pricing:** $24/month (Creator) - 15 minutes/month
- **API:** Available
- **Features:**
  - 100+ avatars
  - Voice cloning
  - Video translation
  - Templates
- **Use Case:** Diverse content types

**Website:** https://www.heygen.com/

### Option 4: Runway ML (Gen-2)
**Best for:** Creative AI video generation

- **Pricing:** $12/month (Standard) - 125 credits
- **API:** Available
- **Features:**
  - Text-to-video
  - Image-to-video
  - Video-to-video
  - Motion brush
- **Use Case:** Abstract concepts, visualizations

**Website:** https://runwayml.com/

---

## 🏗️ Architecture Design

### Backend Components

```
backend/app/services/
├── video_generator.py       # Main video generation service
├── video_cache.py           # Cache generated videos
└── video_templates.py       # Video templates and prompts
```

### Frontend Components

```
frontend/src/
├── components/VideoPlayer.tsx       # Video player component
├── services/videoService.ts         # Video API client
└── hooks/useVideoGeneration.ts      # Video generation hook
```

### Flow Diagram

```
User Query → Biometric Analysis → Content Generation
                                         ↓
                                  Video Generation
                                  (Background Task)
                                         ↓
                                  Cache Video URL
                                         ↓
                                  Send to Frontend
                                         ↓
                                  Display in Player
```

---

## 💻 Implementation

### 1. Backend Service (D-ID Example)

**File:** `backend/app/services/video_generator.py`

```python
"""
AI Video Generation Service
Integrates with D-ID API for educational video creation
"""

import os
import logging
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class VideoGenerator:
    """Generate educational videos using D-ID API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DID_API_KEY")
        self.base_url = "https://api.d-id.com"
        self.cache = {}  # Simple in-memory cache
        
    async def generate_video(
        self,
        script: str,
        avatar_id: str = "amy-jcwCkr1grs",  # Default avatar
        voice_id: str = "en-US-JennyNeural",  # Default voice
        title: str = "Educational Video"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a video from text script
        
        Args:
            script: Text content to be spoken
            avatar_id: D-ID avatar identifier
            voice_id: Voice identifier
            title: Video title
            
        Returns:
            Dict with video_url and metadata
        """
        
        # Check cache first
        cache_key = f"{script[:50]}_{avatar_id}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() < cached['expires']:
                logger.info(f"Returning cached video for: {title}")
                return cached['data']
        
        try:
            # Create video generation request
            async with aiohttp.ClientSession() as session:
                # Step 1: Create talk
                create_url = f"{self.base_url}/talks"
                headers = {
                    "Authorization": f"Basic {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "script": {
                        "type": "text",
                        "input": script,
                        "provider": {
                            "type": "microsoft",
                            "voice_id": voice_id
                        }
                    },
                    "source_url": f"https://create-images-results.d-id.com/DefaultPresenters/{avatar_id}/image.jpeg",
                    "config": {
                        "stitch": True,
                        "result_format": "mp4"
                    }
                }
                
                async with session.post(create_url, json=payload, headers=headers) as response:
                    if response.status != 201:
                        logger.error(f"Failed to create video: {response.status}")
                        return None
                    
                    result = await response.json()
                    talk_id = result.get('id')
                    
                    if not talk_id:
                        logger.error("No talk ID returned")
                        return None
                
                # Step 2: Poll for completion
                status_url = f"{self.base_url}/talks/{talk_id}"
                max_attempts = 60  # 5 minutes max
                attempt = 0
                
                while attempt < max_attempts:
                    await asyncio.sleep(5)  # Wait 5 seconds between checks
                    
                    async with session.get(status_url, headers=headers) as response:
                        if response.status != 200:
                            logger.error(f"Failed to check status: {response.status}")
                            return None
                        
                        status_data = await response.json()
                        status = status_data.get('status')
                        
                        if status == 'done':
                            video_url = status_data.get('result_url')
                            
                            result_data = {
                                'video_url': video_url,
                                'talk_id': talk_id,
                                'title': title,
                                'duration': status_data.get('duration', 0),
                                'created_at': datetime.now().isoformat()
                            }
                            
                            # Cache for 24 hours
                            self.cache[cache_key] = {
                                'data': result_data,
                                'expires': datetime.now() + timedelta(hours=24)
                            }
                            
                            logger.info(f"Video generated successfully: {title}")
                            return result_data
                        
                        elif status == 'error':
                            logger.error(f"Video generation failed: {status_data.get('error')}")
                            return None
                    
                    attempt += 1
                
                logger.error("Video generation timed out")
                return None
                
        except Exception as e:
            logger.error(f"Error generating video: {e}", exc_info=True)
            return None
    
    async def generate_module_video(
        self,
        module_title: str,
        module_content: str,
        cognitive_load: str = "medium"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate video for a teaching module
        
        Args:
            module_title: Module title
            module_content: Module content
            cognitive_load: User's cognitive load
            
        Returns:
            Video data dict
        """
        
        # Prepare script (limit to ~500 words for reasonable video length)
        script = self._prepare_script(module_title, module_content, cognitive_load)
        
        # Select avatar based on content type
        avatar_id = self._select_avatar(module_content)
        
        # Select voice based on cognitive load
        voice_id = self._select_voice(cognitive_load)
        
        return await self.generate_video(
            script=script,
            avatar_id=avatar_id,
            voice_id=voice_id,
            title=module_title
        )
    
    def _prepare_script(
        self,
        title: str,
        content: str,
        cognitive_load: str
    ) -> str:
        """Prepare video script from module content"""
        
        # Clean content
        clean_content = content.replace('•', '-').replace('**', '')
        
        # Limit length based on cognitive load
        max_words = {
            'low': 300,
            'medium': 200,
            'high': 150
        }
        
        words = clean_content.split()
        limited_content = ' '.join(words[:max_words.get(cognitive_load, 200)])
        
        # Create script
        script = f"Hello! Let's learn about {title}. {limited_content}"
        
        return script
    
    def _select_avatar(self, content: str) -> str:
        """Select appropriate avatar based on content"""
        
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['code', 'programming', 'python']):
            return "amy-jcwCkr1grs"  # Tech-friendly avatar
        elif any(word in content_lower for word in ['data', 'science', 'analysis']):
            return "eric-jJKLYPvlr"  # Professional avatar
        else:
            return "amy-jcwCkr1grs"  # Default
    
    def _select_voice(self, cognitive_load: str) -> str:
        """Select voice based on cognitive load"""
        
        voices = {
            'low': 'en-US-JennyNeural',      # Energetic
            'medium': 'en-US-AriaNeural',    # Balanced
            'high': 'en-US-GuyNeural'        # Calm
        }
        
        return voices.get(cognitive_load, 'en-US-AriaNeural')


# Singleton instance
video_generator = VideoGenerator()
```

### 2. Frontend Video Player Component

**File:** `frontend/src/components/VideoPlayer.tsx`

```typescript
/**
 * AI-Generated Video Player Component
 */

import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, Loader } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface VideoPlayerProps {
  videoUrl?: string;
  title: string;
  isGenerating?: boolean;
  onEnded?: () => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  videoUrl,
  title,
  isGenerating = false,
  onEnded,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setProgress((video.currentTime / video.duration) * 100);
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      onEnded?.();
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('ended', handleEnded);
    };
  }, [onEnded]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;

    video.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const toggleFullscreen = () => {
    const video = videoRef.current;
    if (!video) return;

    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      video.requestFullscreen();
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isGenerating) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-8 text-center"
      >
        <Loader className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Generating AI Video
        </h3>
        <p className="text-sm text-gray-600">
          Creating personalized video illustration for "{title}"...
        </p>
        <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
          <div className="bg-blue-600 h-2 rounded-full animate-pulse w-2/3" />
        </div>
      </motion.div>
    );
  }

  if (!videoUrl) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-black rounded-lg overflow-hidden shadow-2xl"
    >
      {/* Video Element */}
      <div className="relative aspect-video">
        <video
          ref={videoRef}
          src={videoUrl}
          className="w-full h-full"
          onClick={togglePlay}
        />

        {/* Play Overlay */}
        <AnimatePresence>
          {!isPlaying && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 cursor-pointer"
              onClick={togglePlay}
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-lg"
              >
                <Play className="w-10 h-10 text-blue-600 ml-1" />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Controls */}
      <div className="bg-gray-900 p-4">
        <div className="flex items-center gap-4">
          {/* Play/Pause */}
          <button
            onClick={togglePlay}
            className="text-white hover:text-blue-400 transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-6 h-6" />
            ) : (
              <Play className="w-6 h-6" />
            )}
          </button>

          {/* Progress Bar */}
          <div className="flex-1">
            <div className="w-full bg-gray-700 rounded-full h-1 cursor-pointer">
              <div
                className="bg-blue-500 h-1 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Time */}
          <span className="text-white text-sm">
            {formatTime(videoRef.current?.currentTime || 0)} /{' '}
            {formatTime(duration)}
          </span>

          {/* Volume */}
          <button
            onClick={toggleMute}
            className="text-white hover:text-blue-400 transition-colors"
          >
            {isMuted ? (
              <VolumeX className="w-6 h-6" />
            ) : (
              <Volume2 className="w-6 h-6" />
            )}
          </button>

          {/* Fullscreen */}
          <button
            onClick={toggleFullscreen}
            className="text-white hover:text-blue-400 transition-colors"
          >
            <Maximize className="w-6 h-6" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default VideoPlayer;
```

### 3. Integration Hook

**File:** `frontend/src/hooks/useVideoGeneration.ts`

```typescript
/**
 * Hook for AI video generation
 */

import { useState, useEffect } from 'react';
import { useAppStore } from '@/store/appStore';

interface VideoData {
  videoUrl: string;
  title: string;
  duration: number;
}

export const useVideoGeneration = (moduleId?: string) => {
  const [videoData, setVideoData] = useState<VideoData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const currentModule = useAppStore((state) => 
    state.knowledgePayload?.teaching_modules.find(m => m.module_id === moduleId)
  );

  useEffect(() => {
    if (!currentModule || !moduleId) return;

    const generateVideo = async () => {
      setIsGenerating(true);
      setError(null);

      try {
        const response = await fetch('/api/generate-video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            module_id: moduleId,
            title: currentModule.title,
            content: currentModule.content,
            cognitive_load: 'medium', // Get from store
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to generate video');
        }

        const data = await response.json();
        setVideoData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsGenerating(false);
      }
    };

    generateVideo();
  }, [moduleId, currentModule]);

  return { videoData, isGenerating, error };
};
```

---

## 📝 Setup Instructions

### 1. Get API Key

1. Sign up at https://www.d-id.com/
2. Get your API key from dashboard
3. Add to `.env`:
   ```
   DID_API_KEY=your_api_key_here
   ```

### 2. Install Dependencies

**Backend:**
```bash
pip install aiohttp
```

**Frontend:**
```bash
npm install lucide-react
```

### 3. Add to Backend

1. Create `backend/app/services/video_generator.py`
2. Add endpoint in `backend/app/main.py`:

```python
from app.services.video_generator import video_generator

@app.post("/api/generate-video")
async def generate_video(request: VideoRequest):
    result = await video_generator.generate_module_video(
        module_title=request.title,
        module_content=request.content,
        cognitive_load=request.cognitive_load
    )
    return result
```

### 4. Add to Frontend

1. Create `VideoPlayer.tsx` component
2. Import in `DynamicUIRenderer.tsx`:

```typescript
import { VideoPlayer } from '@/components/VideoPlayer';
import { useVideoGeneration } from '@/hooks/useVideoGeneration';

// In component:
const { videoData, isGenerating } = useVideoGeneration(currentModule?.module_id);

// In render:
{(videoData || isGenerating) && (
  <div className="mb-6">
    <VideoPlayer
      videoUrl={videoData?.videoUrl}
      title={currentModule?.title || ''}
      isGenerating={isGenerating}
    />
  </div>
)}
```

---

## 💰 Cost Estimation

### D-ID Pricing (Recommended)
- **Lite Plan:** $5.90/month = 20 minutes of video
- **Pro Plan:** $29/month = 100 minutes of video
- **Average video:** 1-2 minutes per module
- **Cost per video:** ~$0.30 (Lite) or ~$0.29 (Pro)

### Monthly Usage Example
- 50 users × 4 modules = 200 videos
- 200 videos × 1.5 min = 300 minutes
- **Cost:** ~$45/month (Pro plan × 3)

---

## 🎯 Next Steps

1. **Sign up for D-ID** and get API key
2. **Implement backend service** (video_generator.py)
3. **Create frontend components** (VideoPlayer.tsx)
4. **Test with one module** first
5. **Add caching** to reduce API calls
6. **Monitor costs** and usage

---

## 🚀 Future Enhancements

- **Video templates** for different content types
- **Custom avatars** matching user preferences
- **Multi-language support** for global users
- **Video thumbnails** for preview
- **Download option** for offline viewing
- **Interactive elements** in videos
- **Analytics** on video engagement

---

## 📚 Resources

- [D-ID API Documentation](https://docs.d-id.com/)
- [Synthesia API Docs](https://docs.synthesia.io/)
- [HeyGen API Docs](https://docs.heygen.com/)
- [Runway ML Docs](https://docs.runwayml.com/)

---

**Ready to implement?** Start with D-ID's free trial to test the integration!