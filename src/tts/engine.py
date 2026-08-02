"""
TTS Engine - Core text-to-speech generation logic.
"""

import re
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import soundfile as sf

from .cache import cache_chunk, get_cached_chunk
from .config import DEFAULT_LANG, DEFAULT_SPEED, DEFAULT_VOICE, SAMPLE_RATE
from .device import get_device

warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

# Max chars per chunk (kokoro context ~512 tokens, ~2500 chars is safe)
CHUNK_SIZE = 2500

# Number of parallel workers for chunk generation
PARALLEL_WORKERS = 4


def split_into_chunks(text: str, max_chars: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks at sentence boundaries."""
    # Split by sentence-ending punctuation
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If single sentence is too long, split by newlines or force split
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # Try splitting by newlines
            parts = sentence.split("\n")
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if len(part) <= max_chars:
                    chunks.append(part)
                else:
                    # Force split long parts
                    for i in range(0, len(part), max_chars):
                        chunks.append(part[i : i + max_chars])
        elif len(current_chunk) + len(sentence) + 1 > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = (current_chunk + " " + sentence).strip()

    if current_chunk:
        chunks.append(current_chunk.strip())

    return [c for c in chunks if c]


class TTSEngine:
    """Kokoro-82M Text-to-Speech Engine."""

    def __init__(self, lang_code: str = DEFAULT_LANG, device: str | None = None):
        from kokoro import KPipeline

        self.device = device or get_device()
        self.lang_code = lang_code
        self.pipeline = KPipeline(
            lang_code=lang_code,
            device=self.device,
            repo_id="hexgrad/Kokoro-82M",
        )
        self._lock = threading.Lock()

    def generate_chunk(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        speed: float = DEFAULT_SPEED,
    ) -> np.ndarray:
        """Generate audio for a single chunk (with caching)."""
        # Check cache first
        cached = get_cached_chunk(text, voice, speed)
        if cached is not None:
            return cached

        # Generate with lock to ensure thread safety on pipeline
        with self._lock:
            generator = self.pipeline(text, voice=voice, speed=speed)
            segments = []

            for _, _, audio in generator:
                segments.append(audio)

        if not segments:
            return np.array([], dtype=np.float32)

        audio = np.concatenate(segments)

        # Cache the result
        cache_chunk(text, voice, speed, audio)

        return audio

    def generate(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        speed: float = DEFAULT_SPEED,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        parallel: bool = True,
    ) -> np.ndarray:
        """Generate audio from text with chunked processing."""
        chunks = split_into_chunks(text)
        total_chunks = len(chunks)

        if total_chunks == 0:
            raise ValueError("No text to process")

        if parallel and total_chunks > 1:
            return self._generate_parallel(chunks, voice, speed, on_progress)
        else:
            return self._generate_sequential(chunks, voice, speed, on_progress)

    def _generate_sequential(
        self,
        chunks: list[str],
        voice: str,
        speed: float,
        on_progress: Optional[Callable[[int, int, str], None]],
    ) -> np.ndarray:
        """Generate audio chunks sequentially."""
        total_chunks = len(chunks)
        audio_parts = []

        for i, chunk in enumerate(chunks):
            if on_progress:
                preview = chunk[:50] + "..." if len(chunk) > 50 else chunk
                on_progress(i + 1, total_chunks, preview)

            audio = self.generate_chunk(chunk, voice=voice, speed=speed)
            if len(audio) > 0:
                audio_parts.append(audio)

        if not audio_parts:
            raise ValueError("No audio generated")

        return np.concatenate(audio_parts)

    def _generate_parallel(
        self,
        chunks: list[str],
        voice: str,
        speed: float,
        on_progress: Optional[Callable[[int, int, str], None]],
    ) -> np.ndarray:
        """Generate audio chunks in parallel using ThreadPoolExecutor."""
        total_chunks = len(chunks)
        audio_parts: dict[int, np.ndarray] = {}
        completed_count = 0
        progress_lock = threading.Lock()

        def process_chunk(idx: int, chunk: str) -> tuple[int, np.ndarray]:
            return idx, self.generate_chunk(chunk, voice=voice, speed=speed)

        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            futures = {
                executor.submit(process_chunk, i, chunk): i
                for i, chunk in enumerate(chunks)
            }

            for future in as_completed(futures):
                idx, audio = future.result()
                audio_parts[idx] = audio

                with progress_lock:
                    completed_count += 1
                    if on_progress:
                        chunk = chunks[idx]
                        preview = chunk[:50] + "..." if len(chunk) > 50 else chunk
                        on_progress(completed_count, total_chunks, preview)

        # Reassemble in order
        ordered_parts = [
            audio_parts[i]
            for i in range(total_chunks)
            if len(audio_parts.get(i, [])) > 0
        ]

        if not ordered_parts:
            raise ValueError("No audio generated")

        return np.concatenate(ordered_parts)

    def generate_to_file(
        self,
        text: str,
        output_path: str | Path,
        voice: str = DEFAULT_VOICE,
        speed: float = DEFAULT_SPEED,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> Path:
        """Generate audio and save to file."""
        audio = self.generate(text, voice=voice, speed=speed, on_progress=on_progress)
        output_path = Path(output_path)
        sf.write(output_path, audio, SAMPLE_RATE)
        return output_path
