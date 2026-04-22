#!/bin/bash
# Извлечь/перекодировать аудио в mp3 mono 128kbps 44100Hz.
# ~57MB/час — разборчивая речь с запасом; если окажется избыточно, снизим.
# Вход — любой контейнер (m4a, mp4, mp3, wav, ogg...).
# Usage: extract_audio.sh input [output.mp3]
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 input.{m4a,mp4,mp3,...} [output.mp3]" >&2
  exit 1
fi

INPUT="$1"
OUTPUT="${2:-${INPUT%.*}.mp3}"

ffmpeg -y -i "$INPUT" -vn -acodec libmp3lame -ac 1 -ar 44100 -b:a 128k "$OUTPUT"
echo "Audio: $OUTPUT"
