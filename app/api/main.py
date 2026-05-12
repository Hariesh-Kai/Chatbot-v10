from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.schemas import (
    CitationResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from app.generation.qa import GroundedAnswerBuilder
from app.ingestion.chunker import StructureAwareChunker
from app.ingestion.parser import DocumentParser
from app.retrieval.index import InMemoryHybridIndex

app = FastAPI(title="Industrial RAG API", version="0.1.0")

parser = DocumentParser()
chunker = StructureAwareChunker()
index = InMemoryHybridIndex()
answer_builder = GroundedAnswerBuilder()




@app.get("/")
def home() -> FileResponse:
    return FileResponse("app/ui/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/documents/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest) -> IngestResponse:
    try:
        blocks = parser.parse(req.file_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    chunks = chunker.chunk(req.document_id, blocks)
    index.upsert(chunks)
    return IngestResponse(document_id=req.document_id, chunks_indexed=len(chunks))




@app.post("/v1/documents/upload", response_model=IngestResponse)
async def upload_document(document_id: str = Form(...), file: UploadFile = File(...)) -> IngestResponse:
    temp_path = f"/tmp/{document_id}_{file.filename}"
    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)
    try:
        blocks = parser.parse(temp_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    chunks = chunker.chunk(document_id, blocks)
    index.upsert(chunks)
    return IngestResponse(document_id=document_id, chunks_indexed=len(chunks))
@app.post("/v1/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    filters = {"document_id": req.document_id, "section": req.section}
    results = index.search(req.question, top_k=req.top_k, filters=filters)
    answer = answer_builder.build(req.question, results)

    if not answer.citations and answer.confidence <= 0.05:
        return QueryResponse(answer=answer.text, confidence=answer.confidence, citations=[])

    citations = [
        CitationResponse(
            document_id=c.document_id,
            chunk_id=c.chunk_id,
            page_start=c.page_start,
            page_end=c.page_end,
            section=c.section,
        )
        for c in answer.citations
    ]
    return QueryResponse(answer=answer.text, confidence=answer.confidence, citations=citations)
