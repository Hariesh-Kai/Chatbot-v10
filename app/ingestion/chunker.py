from __future__ import annotations

from app.core.models import Chunk


class StructureAwareChunker:
    def __init__(self, max_chars: int = 1200, overlap: int = 120) -> None:
        self.max_chars = max_chars
        self.overlap = overlap

    def chunk(self, document_id: str, blocks: list[dict]) -> list[Chunk]:
        chunks: list[Chunk] = []
        count = 0
        for block in blocks:
            text = block["text"]
            start = 0
            while start < len(text):
                end = min(start + self.max_chars, len(text))
                snippet = text[start:end]
                count += 1
                chunks.append(
                    Chunk(
                        chunk_id=f"{document_id}-c{count}",
                        document_id=document_id,
                        content=snippet,
                        metadata={
                            "page_start": block.get("page"),
                            "page_end": block.get("page"),
                            "section": block.get("section"),
                            "element_type": block.get("type"),
                        },
                    )
                )
                if end == len(text):
                    break
                start = max(0, end - self.overlap)
        return chunks
