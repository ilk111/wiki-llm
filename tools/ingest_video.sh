#!/bin/bash
# Видео → транскрипт markdown в один шаг.
# Usage: ingest_video.sh input.mp4 [output.md]
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 input.mp4 [output.md]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT="$1"
OUTPUT="${2:-${INPUT%.*}.md}"

TMP_AUDIO="$(mktemp -t ingest_audio.XXXXXX).mp3"
trap 'rm -f "$TMP_AUDIO"' EXIT

"$SCRIPT_DIR/extract_audio.sh" "$INPUT" "$TMP_AUDIO"

if [ -d "$SCRIPT_DIR/.venv" ]; then
  "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/transcribe.py" "$TMP_AUDIO" "$OUTPUT"
else
  python3 "$SCRIPT_DIR/transcribe.py" "$TMP_AUDIO" "$OUTPUT"
fi
