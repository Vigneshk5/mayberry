"""
FastAPI application and routes.
"""

import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from .state import store, JobStatus
from .tasks import processor
from .documents import extract_text_from_file


app = FastAPI(title="Mayberry TTS")

# Available voices
VOICES = {
    "af_heart": "Heart (American Female)",
    "af_bella": "Bella (American Female)",
    "af_nicole": "Nicole (American Female)",
    "af_sarah": "Sarah (American Female)",
    "af_sky": "Sky (American Female)",
    "am_adam": "Adam (American Male)",
    "am_michael": "Michael (American Male)",
    "bf_emma": "Emma (British Female)",
    "bf_isabella": "Isabella (British Female)",
    "bm_george": "George (British Male)",
    "bm_lewis": "Lewis (British Male)",
}


class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    speed: float = 1.0


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main HTML page."""
    html_path = Path(__file__).parent.parent / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text())


@app.get("/api/voices")
async def list_voices():
    """List available voices."""
    return VOICES


@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    voice: str = Form(default="af_heart"),
    speed: float = Form(default=1.0),
):
    """Upload a document and create a TTS job."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if voice not in VOICES:
        raise HTTPException(status_code=400, detail=f"Invalid voice: {voice}")

    if not (0.5 <= speed <= 2.0):
        raise HTTPException(status_code=400, detail="Speed must be 0.5–2.0")

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        text = extract_text_from_file(tmp_path, file.content_type or "")

        if not text.strip():
            raise HTTPException(
                status_code=400, detail="Could not extract text from document"
            )

        job = store.create_job(
            filename=file.filename, text=text, voice=voice, speed=speed
        )
        processor.enqueue(job.id)

        return {
            "job_id": job.id,
            "filename": job.filename,
            "voice": voice,
            "speed": speed,
            "text_length": len(text),
        }

    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/api/synthesize")
async def synthesize_text(body: SynthesizeRequest):
    """Synthesize text directly without a file upload."""
    if body.voice not in VOICES:
        raise HTTPException(status_code=400, detail=f"Invalid voice: {body.voice}")

    if not (0.5 <= body.speed <= 2.0):
        raise HTTPException(status_code=400, detail="Speed must be 0.5–2.0")

    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is empty")

    display_name = f"{text[:50].replace(chr(10), ' ')}..."
    job = store.create_job(
        filename=display_name, text=text, voice=body.voice, speed=body.speed
    )
    processor.enqueue(job.id)

    return {
        "job_id": job.id,
        "filename": display_name,
        "voice": body.voice,
        "speed": body.speed,
        "text_length": len(text),
    }


@app.get("/api/jobs")
async def list_jobs():
    """List all jobs with logs."""
    jobs = store.list_jobs()
    return [
        {
            "id": j.id,
            "filename": j.filename,
            "voice": j.voice,
            "speed": j.speed,
            "status": j.status.value,
            "progress": j.progress,
            "message": j.message,
            "error": j.error,
            "has_audio": j.audio_path is not None,
            "created_at": j.created_at.isoformat(),
            "total_segments": j.total_segments,
            "current_segment": j.current_segment,
            "text_preview": j.text_preview,
            "duration_sec": j.duration_sec,
            "logs": [
                {"time": log.timestamp.strftime("%H:%M:%S.%f")[:-3], "msg": log.message}
                for log in j.logs[-15:]
            ],
        }
        for j in jobs
    ]


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status with full logs."""
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "filename": job.filename,
        "voice": job.voice,
        "speed": job.speed,
        "status": job.status.value,
        "progress": job.progress,
        "message": job.message,
        "error": job.error,
        "has_audio": job.audio_path is not None,
        "total_segments": job.total_segments,
        "current_segment": job.current_segment,
        "text_preview": job.text_preview,
        "duration_sec": job.duration_sec,
        "logs": [
            {"time": log.timestamp.strftime("%H:%M:%S.%f")[:-3], "msg": log.message}
            for log in job.logs
        ],
    }


@app.get("/api/jobs/{job_id}/download")
async def download_audio(job_id: str):
    """Download generated audio file."""
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    if not job.audio_path:
        raise HTTPException(status_code=404, detail="Audio file not found")

    audio_path = Path(job.audio_path)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    download_name = Path(job.filename).stem + ".wav"

    return FileResponse(
        path=audio_path,
        media_type="audio/wav",
        filename=download_name,
    )


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job."""
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.audio_path:
        Path(job.audio_path).unlink(missing_ok=True)

    store.delete_job(job_id)
    return {"status": "deleted"}
