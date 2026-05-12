from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from app.core.models import Chunk

TOKEN_RE = re.compile(r"[a-zA-Z0-9_./%-]+")


class InMemoryHybridIndex:
    """Reference hybrid retriever: BM25-style sparse + cosine dense surrogate.

    Dense surrogate is term-frequency cosine to keep the implementation dependency-light.
    """

    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}
        self._doc_freq: defaultdict[str, int] = defaultdict(int)
        self._tf: dict[str, Counter[str]] = {}
        self._avg_len = 0.0

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [t.lower() for t in TOKEN_RE.findall(text)]

    def upsert(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk
            tokens = self._tokenize(chunk.content)
            tf = Counter(tokens)
            self._tf[chunk.chunk_id] = tf
            for token in tf.keys():
                self._doc_freq[token] += 1

        total_len = sum(sum(tf.values()) for tf in self._tf.values())
        self._avg_len = total_len / max(1, len(self._tf))

    def _bm25(self, query_tokens: list[str], chunk_id: str, k1: float = 1.5, b: float = 0.75) -> float:
        tf = self._tf[chunk_id]
        doc_len = sum(tf.values())
        n_docs = max(1, len(self._tf))
        score = 0.0
        for token in query_tokens:
            if token not in tf:
                continue
            df = self._doc_freq[token]
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            num = tf[token] * (k1 + 1)
            den = tf[token] + k1 * (1 - b + b * doc_len / max(1e-9, self._avg_len))
            score += idf * (num / den)
        return score

    def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[tuple[Chunk, float]]:
        filters = filters or {}
        query_tokens = self._tokenize(query)
        scored: list[tuple[Chunk, float]] = []
        q_tf = Counter(query_tokens)

        for chunk_id, chunk in self._chunks.items():
            if filters.get("document_id") and chunk.document_id != filters["document_id"]:
                continue
            if filters.get("section") and chunk.metadata.get("section") != filters["section"]:
                continue

            bm25 = self._bm25(query_tokens, chunk_id)
            c_tf = self._tf[chunk_id]
            dot = sum(q_tf[t] * c_tf[t] for t in q_tf.keys())
            qn = math.sqrt(sum(v * v for v in q_tf.values()))
            cn = math.sqrt(sum(v * v for v in c_tf.values()))
            cos = dot / (qn * cn) if qn and cn else 0.0
            score = 0.65 * bm25 + 0.35 * cos
            scored.append((chunk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
