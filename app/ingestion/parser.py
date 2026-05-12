from __future__ import annotations

from pathlib import Path


class DocumentParser:
    """Minimal parser abstraction with TXT fallback.

    In production this class should dispatch to Docling/Unstructured/LlamaParse/OCR.
    """

    SUPPORTED = {".txt", ".md"}

    def parse(self, file_path: str) -> list[dict]:
        path = Path(file_path)
        if path.suffix.lower() not in self.SUPPORTED:
            raise ValueError(f"Unsupported extension {path.suffix}. Use txt/md in this reference implementation.")

        text = path.read_text(encoding="utf-8")
        blocks: list[dict] = []
        for idx, section in enumerate([s.strip() for s in text.split("\n\n") if s.strip()], start=1):
            blocks.append(
                {
                    "type": "paragraph",
                    "text": section,
                    "page": 1,
                    "section": f"Section {idx}",
                }
            )
        return blocks
