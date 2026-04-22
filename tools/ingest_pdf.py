#!/usr/bin/env python3
"""PDF → markdown через Docling (локально, без API)."""
import sys
from pathlib import Path

from docling.document_converter import DocumentConverter


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: ingest_pdf.py file.pdf [output.md]", file=sys.stderr)
        sys.exit(1)

    pdf = Path(sys.argv[1])
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else pdf.with_suffix(".md")

    print(f"Конвертирую {pdf.name}...", file=sys.stderr)
    converter = DocumentConverter()
    result = converter.convert(str(pdf))
    md = result.document.export_to_markdown()

    output.write_text(md, encoding="utf-8")
    print(f"Markdown: {output}")


if __name__ == "__main__":
    main()
