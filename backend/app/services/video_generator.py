"""
Local Video Generator Service
Produces talking-head educational videos entirely on-device.

Pipeline:
  1. Piper TTS  — converts script text to a WAV audio file (fast, CPU-only)
  2. Wav2Lip    — animates a static avatar image with the audio (CPU or GPU)
  3. ffmpeg     — assembles the final MP4

No external API calls are made.  All models are downloaded once and reused.

Environment variables (see .env.example):
  VIDEO_ENABLED          = true | false   (default: false — must opt-in)
  PIPER_BINARY           = path/to/piper binary
  PIPER_MODEL            = path/to/en_US-lessac-medium.onnx
  WAV2LIP_DIR            = path/to/Wav2Lip repo clone
  WAV2LIP_CHECKPOINT     = path/to/wav2lip.pth
  AVATAR_IMAGE           = path/to/avatar.png  (neutral face, ~512×512 px)
  VIDEO_OUTPUT_DIR       = ./data/videos        (where MP4s are stored)
  VIDEO_MAX_CACHE_ITEMS  = 50                   (LRU items kept on disk)
"""

import asyncio
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _required_path(key: str) -> Optional[Path]:
    """Return a Path if the env var is set and the path exists, else None."""
    val = _env(key)
    if not val:
        return None
    p = Path(val)
    if not p.exists():
        logger.warning(f"[VideoGenerator] {key}={val} does not exist – feature disabled")
        return None
    return p


# ---------------------------------------------------------------------------
# VideoGenerationResult
# ---------------------------------------------------------------------------

class VideoGenerationResult:
    """
    Returned by VideoGenerator.generate().
    On success  : success=True,  video_path points to the MP4 file.
    On failure  : success=False, error contains a human-readable reason.
    In mock mode: success=True,  video_path=None, is_mock=True.
    """

    def __init__(
        self,
        success: bool,
        video_path: Optional[Path] = None,
        duration_seconds: float = 0.0,
        generation_time_ms: float = 0.0,
        is_mock: bool = False,
        error: Optional[str] = None,
    ):
        self.success = success
        self.video_path = video_path
        self.duration_seconds = duration_seconds
        self.generation_time_ms = generation_time_ms
        self.is_mock = is_mock
        self.error = error

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "video_path": str(self.video_path) if self.video_path else None,
            "duration_seconds": self.duration_seconds,
            "generation_time_ms": self.generation_time_ms,
            "is_mock": self.is_mock,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# VideoGenerator
# ---------------------------------------------------------------------------

class VideoGenerator:
    """
    Fully local talking-head video generator.

    Usage::

        generator = VideoGenerator()

        # Async (preferred — won't block the event loop)
        result = await generator.generate_async(
            script="Let me explain Python functions...",
            session_id="sess_001"
        )

        # Sync (fine for background threads)
        result = generator.generate(
            script="Let me explain Python functions...",
            session_id="sess_001"
        )
    """

    def __init__(self, config: Optional[dict] = None):
        cfg = config or {}

        self.enabled: bool = (
            cfg.get("enabled", _env("VIDEO_ENABLED", "false")).lower() == "true"
        )

        # --- Piper TTS ---
        self.piper_binary: Optional[Path] = _required_path("PIPER_BINARY") or (
            Path(cfg["piper_binary"]) if cfg.get("piper_binary") else None
        )
        self.piper_model: Optional[Path] = _required_path("PIPER_MODEL") or (
            Path(cfg["piper_model"]) if cfg.get("piper_model") else None
        )

        # --- Wav2Lip ---
        self.wav2lip_dir: Optional[Path] = _required_path("WAV2LIP_DIR") or (
            Path(cfg["wav2lip_dir"]) if cfg.get("wav2lip_dir") else None
        )
        self.wav2lip_checkpoint: Optional[Path] = _required_path("WAV2LIP_CHECKPOINT") or (
            Path(cfg["wav2lip_checkpoint"]) if cfg.get("wav2lip_checkpoint") else None
        )

        # --- Avatar ---
        self.avatar_image: Optional[Path] = _required_path("AVATAR_IMAGE") or (
            Path(cfg["avatar_image"]) if cfg.get("avatar_image") else None
        )

        # --- Output directory ---
        output_dir = _env("VIDEO_OUTPUT_DIR", "./data/videos") or cfg.get(
            "output_dir", "./data/videos"
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # --- Validate readiness ---
        self._ready = self._check_ready()

        if self.enabled and self._ready:
            logger.info(
                "VideoGenerator initialised — Piper TTS + Wav2Lip pipeline ready"
            )
        elif self.enabled and not self._ready:
            logger.warning(
                "VideoGenerator enabled but not all tools are configured. "
                "Running in mock mode. See LOCAL_VIDEO_GUIDE.md for setup."
            )
        else:
            logger.info("VideoGenerator disabled (VIDEO_ENABLED=false)")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(
        self,
        script: str,
        session_id: str,
        voice_pace: str = "normal",
    ) -> VideoGenerationResult:
        """
        Synchronous video generation.  Safe to call from a background thread.

        Args:
            script:      The narration text to speak.
            session_id:  Used for cache key and log correlation.
            voice_pace:  "slow" | "normal" | "fast" — adjusts Piper speaking rate.

        Returns:
            VideoGenerationResult
        """
        if not self.enabled:
            return VideoGenerationResult(
                success=True,
                is_mock=True,
                error="VIDEO_ENABLED=false — video generation skipped",
            )

        if not self._ready:
            return VideoGenerationResult(
                success=True,
                is_mock=True,
                error="Video tools not configured — returning mock result",
            )

        # Check cache first
        cache_key = self._cache_key(script, voice_pace)
        cached = self._cache_lookup(cache_key)
        if cached:
            logger.info(f"[VideoGenerator] Cache hit for session {session_id}")
            return VideoGenerationResult(
                success=True,
                video_path=cached,
                generation_time_ms=0.0,
            )

        start = time.monotonic()
        try:
            with tempfile.TemporaryDirectory(prefix="vidgen_") as tmpdir:
                tmp = Path(tmpdir)
                audio_path = tmp / "speech.wav"
                raw_video_path = tmp / "wav2lip_out.mp4"
                final_path = self.output_dir / f"{cache_key}.mp4"

                logger.info(f"[VideoGenerator] Generating TTS for session {session_id}")
                self._run_piper(script, audio_path, voice_pace)

                logger.info(f"[VideoGenerator] Running Wav2Lip for session {session_id}")
                self._run_wav2lip(audio_path, raw_video_path)

                # Move finished video into persistent output dir
                shutil.move(str(raw_video_path), str(final_path))

        except subprocess.CalledProcessError as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                f"[VideoGenerator] Subprocess failed for session {session_id}: {exc}"
            )
            return VideoGenerationResult(
                success=False,
                generation_time_ms=elapsed,
                error=f"Subprocess error: {exc}",
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                f"[VideoGenerator] Unexpected error for session {session_id}: {exc}",
                exc_info=True,
            )
            return VideoGenerationResult(
                success=False,
                generation_time_ms=elapsed,
                error=str(exc),
            )

        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            f"[VideoGenerator] Done for session {session_id} "
            f"in {elapsed:.0f}ms → {final_path.name}"
        )
        return VideoGenerationResult(
            success=True,
            video_path=final_path,
            generation_time_ms=elapsed,
        )

    async def generate_async(
        self,
        script: str,
        session_id: str,
        voice_pace: str = "normal",
    ) -> VideoGenerationResult:
        """
        Async wrapper — runs the blocking generate() in a thread pool so the
        FastAPI event loop is never blocked during video generation.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.generate, script, session_id, voice_pace
        )

    def is_ready(self) -> bool:
        """Returns True when all tools are present and the generator can produce videos."""
        return self.enabled and self._ready

    def status(self) -> dict:
        """Returns a status dict suitable for the /health endpoint."""
        return {
            "enabled": self.enabled,
            "ready": self._ready,
            "piper_binary": str(self.piper_binary) if self.piper_binary else None,
            "piper_model": str(self.piper_model) if self.piper_model else None,
            "wav2lip_dir": str(self.wav2lip_dir) if self.wav2lip_dir else None,
            "wav2lip_checkpoint": str(self.wav2lip_checkpoint) if self.wav2lip_checkpoint else None,
            "avatar_image": str(self.avatar_image) if self.avatar_image else None,
            "output_dir": str(self.output_dir),
        }

    # ------------------------------------------------------------------
    # Private — Piper TTS
    # ------------------------------------------------------------------

    def _run_piper(self, script: str, output_wav: Path, voice_pace: str) -> None:
        """
        Invoke the Piper binary to synthesise speech.

        Piper reads text from stdin and writes a WAV file to --output_file.
        Speaking rate is controlled by --length_scale:
            slow   → 1.4  (longer pauses, clearer articulation)
            normal → 1.0
            fast   → 0.75
        """
        length_scale = {"slow": "1.4", "fast": "0.75"}.get(voice_pace, "1.0")

        cmd = [
            str(self.piper_binary),
            "--model", str(self.piper_model),
            "--output_file", str(output_wav),
            "--length_scale", length_scale,
            "--sentence_silence", "0.3",
        ]

        result = subprocess.run(
            cmd,
            input=script,
            text=True,
            capture_output=True,
            check=True,
            timeout=120,
        )

        if not output_wav.exists():
            raise RuntimeError(
                f"Piper finished but {output_wav} was not created. "
                f"stderr: {result.stderr}"
            )

        logger.debug(f"[VideoGenerator] Piper produced {output_wav.stat().st_size} bytes")

    # ------------------------------------------------------------------
    # Private — Wav2Lip
    # ------------------------------------------------------------------

    def _run_wav2lip(self, audio_wav: Path, output_mp4: Path) -> None:
        """
        Invoke Wav2Lip's inference.py to produce an animated talking-head video.

        The script lives inside the cloned Wav2Lip repo directory and is called
        as a subprocess so we don't pollute the main Python environment with its
        heavy dependencies (torch, cv2, etc.).
        """
        inference_script = self.wav2lip_dir / "inference.py"
        if not inference_script.exists():
            raise FileNotFoundError(
                f"Wav2Lip inference.py not found at {inference_script}. "
                "Did you clone the Wav2Lip repo? See LOCAL_VIDEO_GUIDE.md."
            )

        cmd = [
            "python", str(inference_script),
            "--checkpoint_path", str(self.wav2lip_checkpoint),
            "--face", str(self.avatar_image),
            "--audio", str(audio_wav),
            "--outfile", str(output_mp4),
            "--nosmooth",         # faster; disable if output is jittery
        ]

        subprocess.run(
            cmd,
            cwd=str(self.wav2lip_dir),
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )

        if not output_mp4.exists():
            raise RuntimeError(
                f"Wav2Lip finished but {output_mp4} was not created."
            )

        logger.debug(f"[VideoGenerator] Wav2Lip produced {output_mp4.stat().st_size} bytes")

    # ------------------------------------------------------------------
    # Private — Cache
    # ------------------------------------------------------------------

    def _cache_key(self, script: str, voice_pace: str) -> str:
        """Deterministic cache key from script text + voice pace."""
        raw = f"{voice_pace}:{script}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:24]

    def _cache_lookup(self, cache_key: str) -> Optional[Path]:
        """Return path to cached video if it exists on disk."""
        candidate = self.output_dir / f"{cache_key}.mp4"
        return candidate if candidate.exists() else None

    # ------------------------------------------------------------------
    # Private — Readiness check
    # ------------------------------------------------------------------

    def _check_ready(self) -> bool:
        """Verify all required components are present."""
        missing = []
        if not self.piper_binary:
            missing.append("PIPER_BINARY")
        if not self.piper_model:
            missing.append("PIPER_MODEL")
        if not self.wav2lip_dir:
            missing.append("WAV2LIP_DIR")
        if not self.wav2lip_checkpoint:
            missing.append("WAV2LIP_CHECKPOINT")
        if not self.avatar_image:
            missing.append("AVATAR_IMAGE")

        # ffmpeg must be on PATH
        if not shutil.which("ffmpeg"):
            missing.append("ffmpeg (not found on PATH)")

        if missing:
            logger.debug(
                f"[VideoGenerator] Missing components: {', '.join(missing)}"
            )
            return False
        return True


# Made with Bob
