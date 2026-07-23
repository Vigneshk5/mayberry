# Mayberry

Local text-to-speech server powered by [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) with hardware acceleration for Apple Silicon (MPS), NVIDIA (CUDA), and CPU fallback.

## Features

- **Web UI** - Upload documents and convert to speech
- **Multiple formats** - Supports `.txt`, `.pdf`, `.docx`, `.md`
- **11 voices** - American/British, male/female options
- **Hardware accelerated** - Apple Silicon MPS, NVIDIA CUDA, or CPU
- **Background processing** - Queue multiple jobs
- **Chunk caching** - Repeated text generates instantly
- **Parallel generation** - Multi-threaded chunk processing

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

```bash
# Clone the repo
git clone https://github.com/your-username/mayberry.git
cd mayberry

# Install dependencies
uv sync

# Or with pip
pip install -e .
```

## Usage

### Start the server

```bash
uv run main.py
```

Then open http://127.0.0.1:8000 in your browser.

### CLI options

```
Usage: python main.py [OPTIONS]

Options:
  -p, --port PORT      Port (default: 8000)
  --host HOST          Host (default: 127.0.0.1)
  -v, --voice VOICE    Voice ID (default: af_heart)
  -l, --lang LANG      Language code (default: a)
  --list-voices        List available voices and exit
```

### Examples

```bash
# Start on a different port
uv run main.py --port 3000

# Use a different voice
uv run main.py --voice am_adam

# List all voices
uv run main.py --list-voices

# Prevent sleep during long processing (macOS)
caffeinate -i uv run main.py
```

## Available Voices

| Category        | Voices                                                    |
| --------------- | --------------------------------------------------------- |
| American Female | `af_heart`, `af_bella`, `af_nicole`, `af_sarah`, `af_sky` |
| American Male   | `am_adam`, `am_michael`                                   |
| British Female  | `bf_emma`, `bf_isabella`                                  |
| British Male    | `bm_george`, `bm_lewis`                                   |

## Language Codes

| Code | Language             |
| ---- | -------------------- |
| `a`  | American English     |
| `b`  | British English      |
| `e`  | Spanish              |
| `f`  | French               |
| `h`  | Hindi                |
| `i`  | Italian              |
| `j`  | Japanese             |
| `p`  | Brazilian Portuguese |
| `z`  | Mandarin Chinese     |

## API Endpoints

| Method   | Endpoint                  | Description                                       |
| -------- | ------------------------- | ------------------------------------------------- |
| `GET`    | `/`                       | Web UI                                            |
| `GET`    | `/api/voices`             | List available voices                             |
| `POST`   | `/api/upload`             | Upload document (multipart form: `file`, `voice`) |
| `GET`    | `/api/jobs`               | List all jobs                                     |
| `GET`    | `/api/jobs/{id}`          | Get job status                                    |
| `GET`    | `/api/jobs/{id}/download` | Download audio                                    |
| `DELETE` | `/api/jobs/{id}`          | Delete job                                        |

## Project Structure

```
mayberry/
├── main.py              # Entry point
├── src/
│   ├── cli.py           # CLI argument parsing
│   ├── server/
│   │   ├── app.py       # FastAPI routes
│   │   ├── tasks.py     # Background job processor
│   │   ├── state.py     # Job state management
│   │   └── documents.py # Document text extraction
│   ├── tts/
│   │   ├── engine.py    # TTS generation engine
│   │   ├── cache.py     # Chunk caching
│   │   ├── config.py    # Voice/language constants
│   │   └── device.py    # Hardware detection
│   └── static/
│       └── index.html   # Web UI
└── pyproject.toml
```

## Performance Tips

- **Larger documents**: Processing is parallelized across chunks
- **Repeated content**: Cached automatically, instant on second run
- **Long sessions**: Use `caffeinate -i` on macOS to prevent sleep
- **Multiple files**: Queue multiple uploads, processed concurrently

## License

MIT
