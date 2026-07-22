"""
In-memory state management for jobs.
Data persists in CLI process, not in browser.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class LogEntry:
    timestamp: datetime
    message: str


@dataclass
class Job:
    id: str
    filename: str
    text: str
    voice: str = "af_heart"
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = ""
    audio_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    logs: list[LogEntry] = field(default_factory=list)
    total_segments: int = 0
    current_segment: int = 0
    text_preview: str = ""


class JobStore:
    """In-memory job storage. Lives as long as the CLI process."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}

    def create_job(self, filename: str, text: str, voice: str = "af_heart") -> Job:
        job_id = str(uuid.uuid4())[:8]
        preview = (
            text[:100].replace("\n", " ") + "..."
            if len(text) > 100
            else text.replace("\n", " ")
        )
        job = Job(
            id=job_id, filename=filename, text=text, voice=voice, text_preview=preview
        )
        self._jobs[job_id] = job
        char_count = len(text)
        self.add_log(
            job_id,
            f"created job_id={job_id} file={filename} size={char_count} voice={voice}",
        )
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def add_log(self, job_id: str, message: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.logs.append(LogEntry(timestamp=datetime.now(), message=message))

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        audio_path: Optional[str] = None,
        error: Optional[str] = None,
        total_segments: Optional[int] = None,
        current_segment: Optional[int] = None,
    ) -> Optional[Job]:
        job = self._jobs.get(job_id)
        if not job:
            return None

        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if message is not None:
            job.message = message
        if audio_path is not None:
            job.audio_path = audio_path
        if error is not None:
            job.error = error
        if total_segments is not None:
            job.total_segments = total_segments
        if current_segment is not None:
            job.current_segment = current_segment

        return job

    def list_jobs(self) -> list[Job]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def delete_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False


# Global store instance
store = JobStore()
