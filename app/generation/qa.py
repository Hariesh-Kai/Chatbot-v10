from __future__ import annotations

from app.core.models import Answer, Citation, Chunk


class GroundedAnswerBuilder:
    def build(self, question: str, results: list[tuple[Chunk, float]]) -> Answer:
        if not results or results[0][1] <= 0:
            return Answer(
                text="Information not confidently found in document.",
                citations=[],
                confidence=0.0,
            )

        top_chunk, score = results[0]
        citations = [
            Citation(
                document_id=top_chunk.document_id,
                chunk_id=top_chunk.chunk_id,
                page_start=top_chunk.metadata.get("page_start"),
                page_end=top_chunk.metadata.get("page_end"),
                section=top_chunk.metadata.get("section"),
            )
        ]

        text = (
            f"Based on the retrieved engineering evidence, the best-supported answer is:\n"
            f"{top_chunk.content[:700]}"
        )

        confidence = min(0.99, max(0.05, score / 5))
        return Answer(text=text, citations=citations, confidence=confidence)
