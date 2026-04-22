#!/usr/bin/env python3
"""Транскрибировать аудио через OpenAI Whisper. Чанкует если файл >24MB."""
import os
import sys
import subprocess
import tempfile
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

MAX_BYTES = 24 * 1024 * 1024  # запас от 25MB лимита Whisper API


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    return float(out.strip())


def split_by_seconds(path: Path, chunk_seconds: int, outdir: Path) -> list[Path]:
    pattern = str(outdir / "chunk_%03d.mp3")
    subprocess.check_call([
        "ffmpeg", "-y", "-i", str(path),
        "-f", "segment",
        "-segment_time", str(chunk_seconds),
        "-c", "copy",
        pattern,
    ])
    return sorted(outdir.glob("chunk_*.mp3"))


def transcribe_one(client: OpenAI, path: Path) -> str:
    with open(path, "rb") as f:
        return client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="ru",
            response_format="text",
        )


def main() -> None:
    load_dotenv(Path(__file__).parent / ".env")

    if len(sys.argv) < 2:
        print("Usage: transcribe.py audio.mp3 [output.md]", file=sys.stderr)
        sys.exit(1)

    audio = Path(sys.argv[1])
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else audio.with_suffix(".md")

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY не задан (см. tools/.env)", file=sys.stderr)
        sys.exit(1)

    client = OpenAI()
    size = audio.stat().st_size

    if size <= MAX_BYTES:
        print(f"Файл {size/1024/1024:.1f}MB — транскрибирую целиком", file=sys.stderr)
        text = transcribe_one(client, audio)
    else:
        duration = ffprobe_duration(audio)
        ratio = MAX_BYTES / size
        chunk_seconds = max(60, int(duration * ratio * 0.95))
        print(
            f"Файл {size/1024/1024:.1f}MB — режу на куски по {chunk_seconds}с",
            file=sys.stderr,
        )
        with tempfile.TemporaryDirectory() as tmp:
            chunks = split_by_seconds(audio, chunk_seconds, Path(tmp))
            parts = []
            for i, chunk in enumerate(chunks, 1):
                print(f"  [{i}/{len(chunks)}] {chunk.name}", file=sys.stderr)
                parts.append(transcribe_one(client, chunk))
            text = "\n\n".join(parts)

    output.write_text(
        f"# Транскрипт: {audio.stem}\n\n{text}\n",
        encoding="utf-8",
    )
    print(f"Transcript: {output}")


if __name__ == "__main__":
    main()
