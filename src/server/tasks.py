"""
Background task processor for TTS jobs with parallel workers.
"""

import tempfile
import threading
import time
import traceback
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, TYPE_CHECKING

from .state import Job, JobStatus, store

if TYPE_CHECKING:
    from src.tts import TTSEngine


class TaskProcessor:
    """Process TTS jobs with multiple workers."""

    def __init__(self, num_workers: int = 2):
        self._queue: Queue[str] = Queue()
        self._workers: list[threading.Thread] = []
        self._num_workers = num_workers
        self._running = False
        self._engine: Optional["TTSEngine"] = None
        self._output_dir = Path(tempfile.mkdtemp(prefix="tts_output_"))
        self._voice = "af_heart"
        self._lang = "a"

    def start(self, voice: str = "af_heart", lang: str = "a"):
        """Start the background processor and preload model."""
        if self._running:
            return

        self._running = True
        self._voice = voice
        self._lang = lang

        print(f"[init] workers={self._num_workers} output_dir={self._output_dir}")
        print(f"[init] loading model repo_id=hexgrad/Kokoro-82M lang={lang}")

        t0 = time.perf_counter()
        from src.tts import TTSEngine

        self._engine = TTSEngine(lang_code=self._lang)
        t1 = time.perf_counter()
        print(
            f"[init] model loaded in {t1 - t0:.2f}s "
            f"(device={self._engine.device} pipelines={self._engine.num_pipelines})"
        )

        for i in range(self._num_workers):
            t = threading.Thread(
                target=self._worker_loop, args=(i,), daemon=True, name=f"worker-{i}"
            )
            t.start()
            self._workers.append(t)

        print(f"[init] {self._num_workers} worker thread(s) started")

    def stop(self):
        """Stop the background processor."""
        self._running = False
        for t in self._workers:
            t.join(timeout=5)
        self._workers.clear()

    def enqueue(self, job_id: str):
        """Add a job to the processing queue."""
        self._queue.put(job_id)
        store.add_log(job_id, f"enqueued queue_size={self._queue.qsize()}")

    def _worker_loop(self, worker_id: int):
        """Worker loop for processing jobs."""
        while self._running:
            try:
                job_id = self._queue.get(timeout=1)
            except Empty:
                continue

            job = store.get_job(job_id)
            if not job:
                continue

            store.add_log(
                job_id, f"dequeued worker={worker_id} tid={threading.get_ident()}"
            )
            self._process_job(job, worker_id)

    def _process_job(self, job: Job, worker_id: int):
        """Process a single TTS job."""
        t_start = time.perf_counter()

        try:
            store.update_job(
                job.id, status=JobStatus.PROCESSING, progress=5, message="init"
            )
            store.add_log(job.id, f"status=PROCESSING")

            text = job.text.strip()
            if not text:
                raise ValueError("empty text content")

            char_count = len(text)
            word_count = len(text.split())
            store.add_log(job.id, f"text chars={char_count} words={word_count}")

            store.update_job(job.id, progress=10, message="chunking")
            store.add_log(job.id, f"voice={job.voice} lang={self._lang}")

            if self._engine is None:
                raise RuntimeError("processor not started")
            engine = self._engine
            output_path = self._output_dir / f"{job.id}.wav"

            # Import here to get chunk count
            from src.tts.engine import split_into_chunks

            chunks = split_into_chunks(text)
            total_chunks = len(chunks)
            store.add_log(job.id, f"chunks={total_chunks} (~2500 chars each)")

            store.update_job(
                job.id, progress=15, message=f"generating 0/{total_chunks}"
            )

            def on_progress(current: int, total: int, preview: str):
                pct = 15 + int((current / total) * 80)
                store.update_job(
                    job.id,
                    progress=pct,
                    message=f"chunk {current}/{total}",
                    total_segments=total,
                    current_segment=current,
                )
                # Log every 5 chunks or first/last
                if current == 1 or current == total or current % 5 == 0:
                    store.add_log(job.id, f"chunk {current}/{total}: {preview[:40]}...")

            t_gen_start = time.perf_counter()
            engine.generate_to_file(
                text=text,
                output_path=output_path,
                voice=job.voice,
                on_progress=on_progress,
            )
            t_gen_end = time.perf_counter()

            file_size = output_path.stat().st_size
            duration_sec = file_size / (24000 * 2)

            store.add_log(job.id, f"generated in {t_gen_end - t_gen_start:.2f}s")
            store.add_log(
                job.id, f"output size={file_size} bytes duration={duration_sec:.1f}s"
            )

            t_end = time.perf_counter()
            store.add_log(job.id, f"completed total_time={t_end - t_start:.2f}s")

            store.update_job(
                job.id,
                status=JobStatus.COMPLETED,
                progress=100,
                message="done",
                audio_path=str(output_path),
            )

        except Exception as e:
            t_end = time.perf_counter()
            error_msg = f"{type(e).__name__}: {e}"
            store.add_log(job.id, f"error {error_msg}")
            store.add_log(job.id, f"failed after {t_end - t_start:.2f}s")
            print(f"[worker-{worker_id}] job={job.id} error: {error_msg}")
            traceback.print_exc()
            store.update_job(
                job.id,
                status=JobStatus.FAILED,
                progress=0,
                message="failed",
                error=error_msg,
            )


# Global processor instance
processor = TaskProcessor(num_workers=4)
