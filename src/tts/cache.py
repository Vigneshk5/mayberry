"""
File-based cache for TTS audio chunks.
"""

import hashlib
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

# Cache directory
CACHE_DIR = Path(tempfile.gettempdir()) / "tts_cache"
CACHE_DIR.mkdir(exist_ok=True)


def _cache_key(text: str, voice: str, speed: float) -> str:
    """Generate a cache key from text, voice, and speed."""
    content = f"{text}|{voice}|{speed}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_cached_chunk(text: str, voice: str, speed: float) -> Optional[np.ndarray]:
    """Get cached audio chunk if it exists."""
    key = _cache_key(text, voice, speed)
    cache_path = CACHE_DIR / f"{key}.npy"

    if cache_path.exists():
        try:
            return np.load(cache_path)
        except Exception:
            # Corrupted cache file, remove it
            cache_path.unlink(missing_ok=True)

    return None


def cache_chunk(text: str, voice: str, speed: float, audio: np.ndarray) -> None:
    """Cache an audio chunk."""
    key = _cache_key(text, voice, speed)
    cache_path = CACHE_DIR / f"{key}.npy"

    try:
        np.save(cache_path, audio)
    except Exception:
        # Ignore cache write errors
        pass


def clear_cache() -> int:
    """Clear all cached chunks. Returns number of files removed."""
    count = 0
    for f in CACHE_DIR.glob("*.npy"):
        try:
            f.unlink()
            count += 1
        except Exception:
            pass
    return count
