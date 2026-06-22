/**
 * BiometricCapture Component
 * Real-time facial landmark detection using MediaPipe Face Mesh
 * Captures biometric data and sends to backend for analysis
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Camera } from '@mediapipe/camera_utils';
import { FaceMesh, Results } from '@mediapipe/face_mesh';
import type { FaceLandmark } from '@/types';

interface BiometricCaptureProps {
  onLandmarksDetected: (landmarks: FaceLandmark[][]) => void;
  onError?: (error: Error) => void;
  isCapturing: boolean;
  captureDuration?: number; // seconds
  fps?: number;
  showVideo?: boolean;
  showOverlay?: boolean;
}

interface CaptureStats {
  framesProcessed: number;
  landmarksDetected: number;
  avgProcessingTime: number;
  captureProgress: number;
}

export const BiometricCapture: React.FC<BiometricCaptureProps> = ({
  onLandmarksDetected,
  onError,
  isCapturing,
  captureDuration = 3,
  fps = 30,
  showVideo = true,
  showOverlay = true,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const faceMeshRef = useRef<FaceMesh | null>(null);
  const cameraRef = useRef<Camera | null>(null);
  const landmarksBufferRef = useRef<FaceLandmark[][]>([]);
  const captureStartTimeRef = useRef<number>(0);
  const processingTimesRef = useRef<number[]>([]);

  const [stats, setStats] = useState<CaptureStats>({
    framesProcessed: 0,
    landmarksDetected: 0,
    avgProcessingTime: 0,
    captureProgress: 0,
  });
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize MediaPipe Face Mesh
  useEffect(() => {
    const initializeFaceMesh = async () => {
      try {
        const faceMesh = new FaceMesh({
          locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
          },
        });

        faceMesh.setOptions({
          maxNumFaces: 1,
          refineLandmarks: true,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5,
        });

        faceMesh.onResults(onResults);
        faceMeshRef.current = faceMesh;
        setIsInitialized(true);
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to initialize Face Mesh');
        setError(error.message);
        onError?.(error);
      }
    };

    initializeFaceMesh();

    return () => {
      if (faceMeshRef.current) {
        faceMeshRef.current.close();
      }
    };
  }, []);

  // Handle Face Mesh results
  const onResults = useCallback((results: Results) => {
    if (!isCapturing) return;

    const startTime = performance.now();

    // Draw results on canvas if overlay is enabled
    if (showOverlay && canvasRef.current && results.image) {
      const canvasCtx = canvasRef.current.getContext('2d');
      if (canvasCtx) {
        canvasCtx.save();
        canvasCtx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
        canvasCtx.drawImage(results.image, 0, 0, canvasRef.current.width, canvasRef.current.height);

        // Draw face mesh
        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
          const landmarks = results.multiFaceLandmarks[0];
          
          // Draw landmarks
          canvasCtx.fillStyle = '#00FF00';
          landmarks.forEach((landmark) => {
            canvasCtx.beginPath();
            canvasCtx.arc(
              landmark.x * canvasRef.current!.width,
              landmark.y * canvasRef.current!.height,
              1,
              0,
              2 * Math.PI
            );
            canvasCtx.fill();
          });
        }

        canvasCtx.restore();
      }
    }

    // Store landmarks
    if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
      const landmarks = results.multiFaceLandmarks[0].map((lm) => ({
        x: lm.x,
        y: lm.y,
        z: lm.z || 0,
      }));

      landmarksBufferRef.current.push(landmarks);

      // Track processing time
      const processingTime = performance.now() - startTime;
      processingTimesRef.current.push(processingTime);

      // Update stats
      const elapsed = (Date.now() - captureStartTimeRef.current) / 1000;
      const progress = Math.min((elapsed / captureDuration) * 100, 100);

      setStats({
        framesProcessed: landmarksBufferRef.current.length,
        landmarksDetected: landmarks.length,
        avgProcessingTime:
          processingTimesRef.current.reduce((a, b) => a + b, 0) / processingTimesRef.current.length,
        captureProgress: progress,
      });

      // Check if capture duration reached
      if (elapsed >= captureDuration) {
        finishCapture();
      }
    }
  }, [isCapturing, captureDuration, showOverlay]);

  // Finish capture and send data
  const finishCapture = useCallback(() => {
    if (landmarksBufferRef.current.length > 0) {
      onLandmarksDetected(landmarksBufferRef.current);
      
      // Reset buffer
      landmarksBufferRef.current = [];
      processingTimesRef.current = [];
      setStats({
        framesProcessed: 0,
        landmarksDetected: 0,
        avgProcessingTime: 0,
        captureProgress: 0,
      });
    }
  }, [onLandmarksDetected]);

  // Start/stop camera
  useEffect(() => {
    if (!isInitialized || !videoRef.current || !faceMeshRef.current) return;

    const startCamera = async () => {
      try {
        const camera = new Camera(videoRef.current!, {
          onFrame: async () => {
            if (faceMeshRef.current && videoRef.current) {
              await faceMeshRef.current.send({ image: videoRef.current });
            }
          },
          width: 640,
          height: 480,
        });

        await camera.start();
        cameraRef.current = camera;

        if (isCapturing) {
          captureStartTimeRef.current = Date.now();
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to start camera');
        setError(error.message);
        onError?.(error);
      }
    };

    if (isCapturing) {
      startCamera();
    }

    return () => {
      if (cameraRef.current) {
        cameraRef.current.stop();
      }
    };
  }, [isInitialized, isCapturing, onError]);

  // Reset capture start time when capturing starts
  useEffect(() => {
    if (isCapturing) {
      captureStartTimeRef.current = Date.now();
    }
  }, [isCapturing]);

  return (
    <div className="biometric-capture">
      <div className="relative">
        {/* Video element (hidden if showVideo is false) */}
        <video
          ref={videoRef}
          className={`${showVideo ? 'block' : 'hidden'} w-full h-auto rounded-lg`}
          playsInline
          style={{ transform: 'scaleX(-1)' }} // Mirror video
        />

        {/* Canvas overlay for landmarks */}
        {showOverlay && (
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 w-full h-full"
            width={640}
            height={480}
            style={{ transform: 'scaleX(-1)' }}
          />
        )}

        {/* Status overlay */}
        {isCapturing && (
          <div className="absolute bottom-4 left-4 right-4 bg-black bg-opacity-70 text-white p-3 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-semibold">Capturing Biometrics...</span>
              <span className="text-sm">{stats.captureProgress.toFixed(0)}%</span>
            </div>
            
            {/* Progress bar */}
            <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${stats.captureProgress}%` }}
              />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <div className="text-gray-400">Frames</div>
                <div className="font-mono">{stats.framesProcessed}</div>
              </div>
              <div>
                <div className="text-gray-400">Landmarks</div>
                <div className="font-mono">{stats.landmarksDetected}</div>
              </div>
              <div>
                <div className="text-gray-400">Avg Time</div>
                <div className="font-mono">{stats.avgProcessingTime.toFixed(1)}ms</div>
              </div>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="absolute top-4 left-4 right-4 bg-red-500 bg-opacity-90 text-white p-3 rounded-lg">
            <div className="font-semibold">Error</div>
            <div className="text-sm">{error}</div>
          </div>
        )}

        {/* Initialization message */}
        {!isInitialized && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75 rounded-lg">
            <div className="text-white text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
              <div>Initializing Face Mesh...</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BiometricCapture;

// Made with Bob for IBM AI Builders Challenge