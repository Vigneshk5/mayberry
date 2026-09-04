<p align="center">
  <img src="./logo.svg" width="96" height="96" alt="Mayberry logo" />
</p>

<h1 align="center">Mayberry</h1>

<p align="center">
  Local, private text-to-speech — no API keys, no cloud, no tracking.<br/>
  Powered by <a href="https://huggingface.co/hexgrad/Kokoro-82M">Kokoro-82M</a>
</p>

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Kokoro-82M](https://img.shields.io/badge/model-Kokoro--82M-orange)](https://huggingface.co/hexgrad/Kokoro-82M)
[![Platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)]()

Turn any document into natural speech on your own machine. Hardware-accelerated on Apple Silicon (MPS) and NVIDIA (CUDA), with CPU fallback. Queue jobs, pick from 11 voices, and download WAV — all from a clean local web UI or a simple REST API.

<!-- Add a screenshot or demo GIF at docs/screenshot.png and uncomment below -->
<!-- ![Mayberry Web UI](docs/screenshot.png) -->
<!-- <p align="center"><img src="docs/demo.gif" width="700" alt="Mayberry demo" /></p> -->

---

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Voices & Languages](#voices--languages)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Development](#development)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [Acknowledgments](#acknowledgments)
- [License](#license)

---

## Features

- **Web UI** — Drag-and-drop documents or paste text, pick a voice, hit synthesize
- **Multiple formats** — `.txt`, `.pdf`, `.docx`, `.md` (auto text extraction)
- **11 voices** — American/British, female/male (see [Voices](#voices--languages))
- **9 languages** — English, Spanish, French, Hindi, Italian, Japanese, Portuguese, Mandarin + variants
- **Hardware accelerated** — Auto-detects `MPS` > `CUDA` > `CPU`; no config needed
- **Background jobs** — Queue multiple docs, poll progress, download when done
- **Chunk caching** — Identical text chunks return instantly on repeat
- **Parallel generation** — Multi-threaded chunk synthesis with thread-safe pipeline
- **Speed control** — `0.5x` – `2.0x` per job
- **100% local** — Model runs on-device; your documents never leave your machine

## Demo

1. Start the server: `uv run main.py`
2. Open http://127.0.0.1:8000
3. Drop a PDF or paste text → choose voice/speed → Download WAV

API one-liner:

```bash
curl -X POST http://127.0.0.1:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello from Mayberry.","voice":"af_heart","speed":1.0}'
```

## Quick Start

Prerequisites: Python 3.10+, [uv](https://github.com/astral-sh/uv) (recommended) or pip.

```bash
git clone https://github.com/Vigneshk5/mayberry.git
cd mayberry

# install (creates .venv and downloads deps)
uv sync

# run — first launch downloads Kokoro-82M (~350 MB) from Hugging Face
uv run main.py

# open http://127.0.0.1:8000
```

> **macOS note:** Keep your Mac awake during long jobs: `caffeinate -i uv run main.py`

## Installation

### Option 1: uv (recommended)

```bash
git clone https://github.com/Vigneshk5/mayberry.git
cd mayberry
uv sync
uv run main.py
```

### Option 2: pip

```bash
git clone https://github.com/Vigneshk5/mayberry.git
cd mayberry
pip install -e .
python main.py
```

### Option 3: pip + venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python main.py
```

### System dependencies

- **Python** `>=3.10`
- **espeak-ng** (required by `misaki` for G2P on some platforms):
  ```bash
  # macOS
  brew install espeak-ng
  # Ubuntu/Debian
  sudo apt-get install espeak-ng
  ```
- No other system deps. `torch` with MPS/CUDA is pulled via `kokoro`.

Model cache: Hugging Face models are cached under `~/.cache/huggingface/` by default.

## Usage

### Web UI

```bash
uv run main.py
# → http://127.0.0.1:8000
```

- **Upload Document** tab — drop `.txt` / `.pdf` / `.docx` / `.md` files (multiple at once)
- **Type Text** tab — paste any text, `⌘+Enter` to synthesize
- Adjust **Voice** and **Speed** per job
- Track progress, stream logs, preview audio, and download `.wav` when `completed`

### CLI

```
Usage: python main.py [OPTIONS]

Options:
  -p, --port PORT      Port (default: 8000)
  --host HOST          Host (default: 127.0.0.1)
  -v, --voice VOICE    Default voice for new jobs (default: af_heart)
  -l, --lang LANG      Language code (default: a)
  --list-voices        List available voices and exit
  -h, --help           Show help
```

Examples:

```bash
# Custom port / host
uv run main.py --port 3000 --host 0.0.0.0

# Default voice for the session
uv run main.py --voice am_adam --lang a

# List voices & languages
uv run main.py --list-voices

# Prevent macOS sleep during batch jobs
caffeinate -i uv run main.py
```

### REST API

Base URL: `http://127.0.0.1:8000`

Upload a document:

```bash
curl -X POST http://127.0.0.1:8000/api/upload \
  -F "file=@paper.pdf" \
  -F "voice=af_heart" \
  -F "speed=1.0"
# → {"job_id":"a1b2c3d4","filename":"paper.pdf","voice":"af_heart","speed":1.0,"text_length":48210}
```

Synthesize raw text:

```bash
curl -X POST http://127.0.0.1:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Your text here.","voice":"bf_emma","speed":1.1}'
```

Poll jobs:

```bash
curl http://127.0.0.1:8000/api/jobs
curl http://127.0.0.1:8000/api/jobs/a1b2c3d4
```

Download audio:

```bash
curl -o out.wav http://127.0.0.1:8000/api/jobs/a1b2c3d4/download
```

Delete a job:

```bash
curl -X DELETE http://127.0.0.1:8000/api/jobs/a1b2c3d4
```

## Voices & Languages

### Voices (11)

| Category        | Voices                                                    | Accent   |
| --------------- | --------------------------------------------------------- | -------- |
| American Female | `af_heart` (default), `af_bella`, `af_nicole`, `af_sarah`, `af_sky` | US |
| American Male   | `am_adam`, `am_michael`                                   | US       |
| British Female  | `bf_emma`, `bf_isabella`                                  | UK       |
| British Male    | `bm_george`, `bm_lewis`                                   | UK       |

Preview voices from the Web UI dropdown or via `GET /api/voices`.

### Languages

| Code | Language             | Code | Language             |
| ---- | -------------------- | ---- | -------------------- |
| `a`  | American English (default) | `h`  | Hindi                |
| `b`  | British English      | `i`  | Italian              |
| `e`  | Spanish              | `j`  | Japanese             |
| `f`  | French               | `p`  | Brazilian Portuguese |
|      |                      | `z`  | Mandarin Chinese     |

> Voices are trained primarily for `a`/`b`. Cross-language synthesis works but quality varies — prefer matching voice accent to language code (e.g., `bf_emma` + `b`).

## API Reference

| Method   | Endpoint                  | Description |
| -------- | ------------------------- | ----------- |
| `GET`    | `/`                       | Web UI (`index.html`) |
| `GET`    | `/api/voices`             | List voices → `{ "af_heart": "Heart (American Female)", ... }` |
| `POST`   | `/api/upload`             | Upload document. Multipart: `file` (required), `voice` (default `af_heart`), `speed` (`0.5–2.0`) |
| `POST`   | `/api/synthesize`         | Synthesize raw text. JSON: `{ text, voice?, speed? }` |
| `GET`    | `/api/jobs`               | List all jobs (with recent logs) |
| `GET`    | `/api/jobs/{id}`          | Get job status + full logs |
| `GET`    | `/api/jobs/{id}/download` | Download WAV (only when `completed`) |
| `DELETE` | `/api/jobs/{id}`          | Delete job and its audio file |

**Job object** (abridged):

```json
{
  "id": "a1b2c3d4",
  "filename": "paper.pdf",
  "voice": "af_heart",
  "speed": 1.0,
  "status": "processing",
  "progress": 42,
  "total_segments": 18,
  "current_segment": 8,
  "duration_sec": 12.4,
  "has_audio": false,
  "logs": [{"time":"14:02:11.042","msg":"chunk 8/18 done"}]
}
```

`status`: `pending` → `processing` → `completed` | `failed`

Errors use standard HTTP codes with `{"detail": "..."}`.

## Configuration

| Flag / Field | Default | Notes |
| ------------ | ------- | ----- |
| `--voice` / `voice` | `af_heart` | Must be in `GET /api/voices` |
| `--lang` | `a` | Language code for the Kokoro pipeline |
| `speed` | `1.0` | Per-job, `0.5`–`2.0`. Affects pitch + duration |
| `--port` | `8000` | |
| `--host` | `127.0.0.1` | Use `0.0.0.0` to expose on LAN |

Environment:

- `PYTORCH_ENABLE_MPS_FALLBACK=1` is set automatically for Apple Silicon.
- Model repo is fixed to `hexgrad/Kokoro-82M` (see `src/tts/engine.py:81`).

Tuning constants (`src/tts/engine.py:23`):

- `CHUNK_SIZE = 2500` chars — max chars per synthesis chunk (sentence-aware)
- `PARALLEL_WORKERS = 4` — threads for parallel chunk generation

## Project Structure

```
mayberry/
├── main.py              # Entry point — delegates to src.cli:run
├── pyproject.toml       # Deps & build config (hatchling)
├── src/
│   ├── cli.py           # argparse + uvicorn launch
│   ├── server/
│   │   ├── app.py       # FastAPI routes (/, /api/*)
│   │   ├── state.py     # In-memory JobStore + JobStatus
│   │   ├── tasks.py     # Background TaskProcessor (queue + workers)
│   │   └── documents.py # Text extraction for txt/pdf/docx/md
│   ├── tts/
│   │   ├── engine.py    # TTSEngine: chunking, caching, Kokoro pipeline
│   │   ├── cache.py     # File-based chunk cache
│   │   ├── config.py    # Voices, languages, defaults
│   │   └── device.py    # MPS / CUDA / CPU auto-detection
│   └── static/
│       └── index.html   # Single-file Web UI (no build step)
└── uv.lock
```

## How It Works

1. **Extract** — `documents.py` pulls text from PDF (`pypdf`), DOCX (`python-docx`), or plain text.
2. **Chunk** — `engine.py:29` splits on sentence boundaries into ~2500-char chunks.
3. **Synthesize** — Each chunk goes through `KPipeline` (Kokoro-82M) on the best available device (`device.py:10`). A `threading.Lock` ensures MPS safety; `ThreadPoolExecutor` parallelizes chunks.
4. **Cache** — `cache.py` memoizes chunk audio by `(text, voice, speed)` hash so repeated text is instant.
5. **Queue** — `tasks.py` / `state.py` manage an in-memory job queue with worker threads, progress callbacks, and log streaming to the UI.

Audio is written as 24 kHz WAV (`config.py:5` `SAMPLE_RATE = 24000`).

## Development

```bash
# setup
uv sync

# run with auto-reload (dev)
uv run uvicorn src.server.app:app --reload --port 8000

# lint / format (if ruff is installed)
uv run ruff check src/
uv run ruff format src/

# type check (if mypy/pyright is installed)
uv run mypy src/
```

No test suite yet — contributions adding `pytest` coverage are welcome.

## Contributing

Contributions are welcome! This is a small, focused codebase — great for first PRs.

1. Fork the repo and create a feature branch: `git checkout -b feat/my-feature`
2. Make your change with clear commit messages
3. Test manually: `uv run main.py` + try upload + synthesize + download
4. Open a pull request — describe what you changed and why

Ideas for contributors:

- [ ] Add `pytest` + CI (GitHub Actions)
- [ ] Docker image + `docker-compose.yml`
- [ ] More voices / language presets in the UI
- [ ] Streaming audio response (chunked transfer)
- [ ] Export to MP3/OGG in addition to WAV
- [ ] Persistent job store (SQLite) so jobs survive restarts

Please open an issue first for large changes so we can discuss design.

See also: `CONTRIBUTING.md` (coming soon) and our [issue tracker](https://github.com/Vigneshk5/mayberry/issues).

## Troubleshooting

| Problem | Fix |
| ------- | --- |
| `No module named 'kokoro'` / install fails | Ensure Python ≥3.10 and `uv sync` completed. On Apple Silicon, use a native (arm64) Python. |
| `espeak-ng` / `misaki` errors | `brew install espeak-ng` (macOS) or `sudo apt-get install espeak-ng` (Linux). |
| Model download stalls | First run downloads ~350 MB from Hugging Face. Check `~/.cache/huggingface/` and network. Retry `uv run main.py`. |
| `Address already in use` | `uv run main.py --port 3000` or `lsof -i :8000; kill <pid>`. |
| PDF extracts no text | Scanned PDFs need OCR — try converting to `.txt` first or use an OCR tool. |
| MPS errors on Mac | `PYTORCH_ENABLE_MPS_FALLBACK=1` is already set (`device.py:5`). Falls back to CPU automatically. |
| Out of memory | Reduce `PARALLEL_WORKERS` in `engine.py:26` or process smaller documents. |
| Audio too fast/slow | Adjust `speed` `0.5–2.0` in UI or API. Default `1.0` is most natural. |

## Acknowledgments

- [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) by Hexgrad — the excellent open TTS model that powers Mayberry
- [misaki](https://github.com/hexgrad/misaki) for G2P
- [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- Inspired by the need for private, offline document-to-speech

## License

Apache 2.0 — see [LICENSE](LICENSE). Kokoro-82M weights are under [Apache 2.0](https://huggingface.co/hexgrad/Kokoro-82M) as well.

---

<p align="center">Made for reading without looking. If Mayberry helps you, give it a ⭐ on GitHub.</p>
