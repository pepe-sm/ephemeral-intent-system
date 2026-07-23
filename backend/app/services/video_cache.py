"""
Video Cache Service
LRU on-disk cache for generated MP4 files.

Keeps the newest VIDEO_MAX_CACHE_ITEMS videos on disk and evicts the oldest
ones when the limit is exceeded.  No external dependency — pure Python + pathlib.

The VideoGenerator itself handles cache lookup and storage via cache keys.
This module provides the optional eviction / housekeeping step that should be
called periodically (e.g., on session termination or startup).
"""

import logging
import os
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 50


class VideoCache:
    """
    Manages the on-disk LRU cache for generated video files.

    Args:
        cache_dir:  Directory where MP4 files are stored.
        max_items:  Maximum number of video files to keep.
                    Oldest files (by modification time) are removed first.

    Example::

        cache = VideoCache(cache_dir="./data/videos", max_items=50)
        cache.evict_oldest()          # call after each generation
        stats = cache.stats()
    """

    def __init__(
        self,
        cache_dir: str = "./data/videos",
        max_items: int = DEFAULT_MAX_ITEMS,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_items = int(
            os.getenv("VIDEO_MAX_CACHE_ITEMS", str(max_items))
        )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def evict_oldest(self) -> int:
        """
        Remove the oldest files if the cache exceeds max_items.

        Returns:
            Number of files removed.
        """
        videos = self._sorted_videos()
        excess = len(videos) - self.max_items
        if excess <= 0:
            return 0

        to_remove = videos[:excess]  # oldest first
        removed = 0
        for path in to_remove:
            try:
                path.unlink()
                removed += 1
                logger.debug(f"[VideoCache] Evicted {path.name}")
            except OSError as exc:
                logger.warning(f"[VideoCache] Failed to evict {path.name}: {exc}")

        if removed:
            logger.info(f"[VideoCache] Evicted {removed} old video(s)")
        return removed

    def clear_all(self) -> int:
        """Remove every video file in the cache directory."""
        videos = self._sorted_videos()
        removed = 0
        for path in videos:
            try:
                path.unlink()
                removed += 1
            except OSError as exc:
                logger.warning(f"[VideoCache] Failed to remove {path.name}: {exc}")
        logger.info(f"[VideoCache] Cleared {removed} video(s)")
        return removed

    def stats(self) -> dict:
        """Return current cache statistics."""
        videos = self._sorted_videos()
        total_bytes = sum(v.stat().st_size for v in videos)
        return {
            "cache_dir": str(self.cache_dir),
            "max_items": self.max_items,
            "current_items": len(videos),
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        }

    def list_videos(self) -> List[dict]:
        """Return metadata for every cached video, newest first."""
        result = []
        for path in reversed(self._sorted_videos()):
            stat = path.stat()
            result.append(
                {
                    "filename": path.name,
                    "path": str(path),
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime,
                }
            )
        return result

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _sorted_videos(self) -> List[Path]:
        """Return all .mp4 files sorted by modification time (oldest first)."""
        videos = list(self.cache_dir.glob("*.mp4"))
        videos.sort(key=lambda p: p.stat().st_mtime)
        return videos


# Made with Bob
