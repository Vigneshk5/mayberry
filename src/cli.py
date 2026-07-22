"""
Command-line interface for TTS web server.
"""

import argparse

from .tts import VOICES, LANGUAGES
from .tts.config import DEFAULT_LANG, DEFAULT_VOICE


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Kokoro-82M Text-to-Speech Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--voice",
        "-v",
        type=str,
        default=DEFAULT_VOICE,
        help=f"Voice ID (default: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--lang",
        "-l",
        type=str,
        default=DEFAULT_LANG,
        help=f"Language code (default: {DEFAULT_LANG})",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available voices and exit",
    )

    return parser.parse_args()


def print_voices() -> None:
    """Print available voices."""
    print("Available voices:\n")
    for category, voices in VOICES.items():
        label = category.replace("_", " ").title()
        print(f"  {label}:")
        print(f"    {', '.join(voices)}\n")

    print("Language codes:\n")
    for code, name in LANGUAGES.items():
        print(f"  {code} = {name}")


def run() -> None:
    """Main CLI entry point."""
    args = parse_args()

    if args.list_voices:
        print_voices()
        return

    import uvicorn
    from .server import app, processor

    processor.start(voice=args.voice, lang=args.lang)

    print(f"Server: http://{args.host}:{args.port}")
    print(f"Voice:  {args.voice}")
    print(f"Lang:   {args.lang}")
    print("Press Ctrl+C to stop\n")

    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    finally:
        processor.stop()
