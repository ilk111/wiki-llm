#!/usr/bin/env python3
"""Валидатор цитат: проверяет что все > blockquotes в result.md действительно есть в raw.md.

Использование:
    validate_quotes.py <result.md> <raw.md>

Возвращает exit 0 если все цитаты найдены, exit 1 если есть галлюцинации.
Печатает в stderr каждую проблемную цитату с причиной.

Алгоритм:
- Извлекает все > blockquotes из result.md (многострочные склеивает).
- Нормализует тексты: NFKC, lower, удаляет пунктуацию, схлопывает пробелы.
- Для каждой цитаты пробует: (1) прямой substring → ok; (2) разбивает цитату на
  фразы по .!?… и считает долю фраз (≥5 слов) которые нашлись в raw. Если ≥60%
  — считает цитату ок с пометкой partial. Иначе — hallucination.
- Дополнительно: ищет паттерны типа «(стр. N)», «(страница N)», «(p. N)»
  и если raw.md не содержит подобных маркеров вообще — помечает такие
  атрибуции как подозрительные (фабрикация тайм-кодов/страниц).
"""

import re
import sys
import unicodedata
from pathlib import Path


PAGE_ATTR_RE = re.compile(
    r"\(\s*(?:стр\.?|страница|page|p\.?|pp\.?)\s*\d+[^)]*\)",
    flags=re.IGNORECASE,
)
TIMECODE_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
SENTENCE_SPLIT_RE = re.compile(r"[.!?…]+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_blockquotes(md_text: str) -> list[str]:
    quotes: list[str] = []
    current: list[str] = []
    for line in md_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(">"):
            current.append(stripped[1:].strip())
        else:
            if current:
                quotes.append(" ".join(x for x in current if x))
                current = []
    if current:
        quotes.append(" ".join(x for x in current if x))
    return [q for q in quotes if q.strip()]


def sentence_chunks(text: str, min_words: int = 5) -> list[str]:
    chunks = SENTENCE_SPLIT_RE.split(text)
    return [c.strip() for c in chunks if len(c.strip().split()) >= min_words]


def check_quote(quote: str, raw_norm: str) -> tuple[str, str]:
    """Возвращает (status, detail). status ∈ {ok, partial, hallucination}."""
    q_norm = normalize(quote)
    if not q_norm:
        return "ok", "пустая"
    if q_norm in raw_norm:
        return "ok", "substring match"
    chunks = sentence_chunks(q_norm)
    if not chunks:
        return "hallucination", "нет substring match и нет осмысленных фрагментов ≥5 слов"
    hits = sum(1 for c in chunks if c in raw_norm)
    ratio = hits / len(chunks)
    if ratio >= 0.6:
        return "partial", f"{hits}/{len(chunks)} фрагментов найдены ({ratio:.0%})"
    return "hallucination", f"только {hits}/{len(chunks)} фрагментов найдены ({ratio:.0%})"


def check_attributions(quote: str, raw_text: str) -> list[str]:
    """Ищет подозрительные атрибуции страниц/таймкодов которых нет в raw."""
    problems = []
    page_attrs = PAGE_ATTR_RE.findall(quote)
    if page_attrs and not PAGE_ATTR_RE.search(raw_text):
        problems.append(
            f"атрибуции страниц {page_attrs} в цитате, но в raw нет ни одного упоминания страниц"
        )
    tc_attrs = TIMECODE_RE.findall(quote)
    if tc_attrs and not TIMECODE_RE.search(raw_text):
        problems.append(
            f"таймкоды {tc_attrs} в цитате, но в raw нет ни одного таймкода"
        )
    return problems


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: validate_quotes.py <result.md> <raw.md>", file=sys.stderr)
        return 2

    result_path = Path(sys.argv[1])
    raw_path = Path(sys.argv[2])

    if not result_path.exists():
        print(f"ERROR: result not found: {result_path}", file=sys.stderr)
        return 2
    if not raw_path.exists():
        print(f"ERROR: raw not found: {raw_path}", file=sys.stderr)
        return 2

    result_text = result_path.read_text(encoding="utf-8")
    raw_text = raw_path.read_text(encoding="utf-8")
    raw_norm = normalize(raw_text)

    quotes = extract_blockquotes(result_text)
    if not quotes:
        print(f"OK: в {result_path.name} нет blockquote-цитат — нечего валидировать")
        return 0

    hallucinations: list[tuple[str, str]] = []
    partials: list[tuple[str, str]] = []
    attribution_problems: list[tuple[str, list[str]]] = []

    for q in quotes:
        status, detail = check_quote(q, raw_norm)
        if status == "hallucination":
            hallucinations.append((q, detail))
        elif status == "partial":
            partials.append((q, detail))
        attr_problems = check_attributions(q, raw_text)
        if attr_problems:
            attribution_problems.append((q, attr_problems))

    print(
        f"Цитат всего: {len(quotes)}, "
        f"ok: {len(quotes) - len(hallucinations) - len(partials)}, "
        f"partial: {len(partials)}, hallucination: {len(hallucinations)}, "
        f"с атрибуционными проблемами: {len(attribution_problems)}"
    )

    if partials:
        print("\n--- Частичные совпадения (проверить вручную) ---", file=sys.stderr)
        for q, detail in partials:
            preview = q[:120].replace("\n", " ")
            print(f"[partial] {detail}\n    → {preview}...", file=sys.stderr)

    if hallucinations:
        print("\n--- ГАЛЛЮЦИНАЦИИ ---", file=sys.stderr)
        for q, detail in hallucinations:
            preview = q[:160].replace("\n", " ")
            print(f"[hallucination] {detail}\n    → {preview}...", file=sys.stderr)

    if attribution_problems:
        print("\n--- Фабрикация атрибуций (страницы/таймкоды) ---", file=sys.stderr)
        for q, problems in attribution_problems:
            preview = q[:120].replace("\n", " ")
            print(f"[attribution] {'; '.join(problems)}\n    → {preview}...", file=sys.stderr)

    if hallucinations or attribution_problems:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
