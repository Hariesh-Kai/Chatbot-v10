# Industrial RAG (Reference Implementation)

This repository now contains an executable baseline implementation of the industrial RAG architecture described in `INDUSTRIAL_RAG_ARCHITECTURE.md`.

## Run

```bash
pip install -e .
uvicorn app.api.main:app --reload
```

## Test

```bash
python -m pytest -q
```

## Implemented now

- FastAPI service with ingestion + query endpoints.
- Structure-aware chunking with metadata.
- Hybrid in-memory retrieval (BM25-style + cosine blending).
- Grounded answer builder with citation objects and low-confidence fallback.
