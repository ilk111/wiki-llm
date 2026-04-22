#!/bin/bash
# Обработать аудио/видео источник: перекодировать → транскрибировать.
#
# Вход — любой аудио/видео файл (m4a, mp4, mp3, wav, ogg...).
# Результат:
#   <output>.mp3 — сжатая копия mono 64kbps 22050Hz (для переслушивания)
#   <output>.md  — транскрипт Whisper
#
# Оригинал НЕ удаляется автоматически. Скрипт напомнит удалить его
# после того как проверишь транскрипт.
#
# Usage: ingest_audio.sh input [output_basename]
#   input            — путь к исходнику
#   output_basename  — путь без расширения (по умолчанию: рядом с входом)
#
# Пример:
#   tools/ingest_audio.sh vault/raw/qna/efir-2024-03.m4a
#   → vault/raw/qna/efir-2024-03.mp3
#   → vault/raw/qna/efir-2024-03.md
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 input.{m4a,mp4,mp3,...} [output_basename]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT="$1"

if [ $# -ge 2 ]; then
  BASE="$2"
  BASE="${BASE%.md}"
  BASE="${BASE%.mp3}"
else
  BASE="${INPUT%.*}"
fi

OUTPUT_MP3="${BASE}.mp3"
OUTPUT_MD="${BASE}.md"

echo "== Перекодировка =="
"$SCRIPT_DIR/extract_audio.sh" "$INPUT" "$OUTPUT_MP3"

echo
echo "== Транскрипция =="
if [ -d "$SCRIPT_DIR/.venv" ]; then
  "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/transcribe.py" "$OUTPUT_MP3" "$OUTPUT_MD"
else
  python3 "$SCRIPT_DIR/transcribe.py" "$OUTPUT_MP3" "$OUTPUT_MD"
fi

INPUT_SIZE=$(du -h "$INPUT" | cut -f1)
MP3_SIZE=$(du -h "$OUTPUT_MP3" | cut -f1)

echo
echo "== Готово =="
echo "  Транскрипт:  $OUTPUT_MD"
echo "  Аудио-копия: $OUTPUT_MP3 ($MP3_SIZE)"
echo "  Оригинал:    $INPUT ($INPUT_SIZE)"
echo
echo "Проверь транскрипт. Если всё ок — удали оригинал:"
echo "  rm \"$INPUT\""
