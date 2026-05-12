from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Citation:
    document_id: str
    chunk_id: str
    page_start: int | None
    page_end: int | None
    section: str | None


@dataclass(slots=True)
class Answer:
    text: str
    citations: list[Citation]
    confidence: float
