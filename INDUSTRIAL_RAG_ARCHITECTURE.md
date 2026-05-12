# Enterprise Industrial RAG Platform Blueprint

## 1) Full Enterprise Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Channels                               │
│  Web UI (React) | API Clients | Teams/Slack Bot | Batch Jobs | SDKs        │
└───────────────┬─────────────────────────────────────────────────────────────┘
                │ HTTPS + OAuth2/JWT + mTLS (service-to-service)
┌───────────────▼─────────────────────────────────────────────────────────────┐
│                             API Gateway / WAF                              │
│  Rate limiting | authn/authz | request shaping | audit headers             │
└───────────────┬─────────────────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────────────────┐
│                           FastAPI Orchestration Layer                      │
│  /ingest | /query | /chat | /citations | /documents | /admin               │
│  Streaming (SSE/WebSocket), policy checks, tenancy, prompt guards          │
└───────────────┬───────────────────────────────┬─────────────────────────────┘
                │                               │
     ┌──────────▼──────────┐         ┌──────────▼──────────┐
     │ Async Ingestion Svc │         │     Query/RAG Svc   │
     │ (Celery/Arq workers)│         │ (retrieval + answer)│
     └──────────┬──────────┘         └──────────┬──────────┘
                │                               │
       ┌────────▼────────────┐          ┌───────▼────────────────────┐
       │Parsing/OCR/Vision   │          │Retriever + Reranker Engine │
       │Docling/Unstructured │          │Dense+Sparse+Hybrid+Filters │
       │LlamaParse/PyMuPDF   │          │Cross-encoder rerank        │
       └────────┬────────────┘          └───────┬────────────────────┘
                │                               │
        ┌───────▼────────┐             ┌────────▼─────────┐
        │ Chunk & Meta   │             │ LLM Answer Svc    │
        │ Builder        │             │ grounded generation│
        └───────┬────────┘             └────────┬──────────┘
                │                               │
      ┌─────────▼───────────────────────────────▼──────────────────────────┐
      │ Data Plane                                                          │
      │ PostgreSQL + PGVector | Redis | Object Store (S3/MinIO)            │
      │ Optional Qdrant for high-scale ANN                                 │
      │ OpenSearch/Elasticsearch for BM25 and lexical expansion             │
      └─────────┬────────────────────────────────────────────────────────────┘
                │
      ┌─────────▼────────────────────────────────────────────────────────────┐
      │ Observability + Security                                             │
      │ OpenTelemetry | Prometheus | Grafana | Loki | SIEM | Vault KMS      │
      └───────────────────────────────────────────────────────────────────────┘
```

## 2) Recommended Folder Structure

```text
industrial-rag/
  apps/
    api/
      main.py
      routers/
        ingest.py
        query.py
        chat.py
        documents.py
      dependencies/
      middleware/
      schemas/
    workers/
      ingest_worker.py
      embed_worker.py
      ocr_worker.py
      retry_worker.py
  core/
    config/
    security/
    telemetry/
    tenancy/
  ingestion/
    parsers/
      pdf_docling.py
      pdf_pymupdf.py
      unstructured_loader.py
      llamaparse_loader.py
      docx_loader.py
      xlsx_loader.py
      html_loader.py
      xml_loader.py
    ocr/
      paddle_or_tesseract.py
      layout_parser.py
      diagram_detector.py
    normalize/
      units.py
      abbreviations.py
      revision_extractor.py
      standards_extractor.py
    chunking/
      section_chunker.py
      table_chunker.py
      semantic_chunker.py
      adaptive_chunker.py
  retrieval/
    embeddings/
      model_registry.py
      dense_embedder.py
      sparse_encoder.py
      multivector_encoder.py
    index/
      pgvector_repo.py
      bm25_repo.py
      hybrid_search.py
    rerank/
      bge_reranker.py
      cross_encoder.py
    query_expansion/
      multiquery.py
      acronym_expansion.py
  generation/
    prompts/
    answer_builder.py
    citation_builder.py
    confidence.py
    verifier.py
  memory/
    conversation_store.py
    topic_state.py
  storage/
    postgres/
      migrations/
      models/
    redis/
    object_store/
  deployments/
    docker/
    k8s/
    helm/
  tests/
    unit/
    integration/
    eval/
      golden_sets/
      ragas/
      retrieval_bench/
  docs/
    architecture.md
    runbooks/
```

## 3) Chunking Pipeline

1. Parse document into **layout blocks** (heading, paragraph, table, figure, caption, footer).
2. Build **hierarchy graph**: document → section → subsection → element.
3. Apply chunk policy by element type:
   - Text: 350–900 tokens adaptive window, 12–18% overlap.
   - Tables: keep entire table with header repeated in each split row-group chunk.
   - Formula blocks: no intra-formula splitting.
   - Captions/figures: bind caption + nearby text into one multimodal chunk.
4. Add parent references (`parent_section_id`, `breadcrumb`).
5. Attach normalized units and extracted engineering entities.
6. Deduplicate chunks using MinHash + embedding cosine threshold.

## 4) Metadata Schema (Chunk-level)

```json
{
  "tenant_id": "uuid",
  "document_id": "uuid",
  "chunk_id": "uuid",
  "doc_title": "string",
  "doc_type": "BOD|FEED|P&ID|EPC|...",
  "revision": "string",
  "revision_date": "date",
  "discipline": "process|mechanical|electrical|instrumentation|subsea|...",
  "equipment": ["separator", "compressor", "pipeline"],
  "section": "4.2 Design Pressure",
  "subsection": "4.2.1 MAWP",
  "page_start": 20,
  "page_end": 21,
  "table_id": "tbl-4-2",
  "figure_id": "fig-7",
  "standards": ["ASME VIII", "API 14C"],
  "units": ["bar", "degC", "mm"],
  "numeric_values": [{"name": "MAWP", "value": 125.0, "unit": "bar"}],
  "abbreviations": ["MAWP", "FPSO", "WAG"],
  "source_uri": "s3://bucket/doc.pdf",
  "content_hash": "sha256",
  "ingest_version": "v1.6.0"
}
```

## 5) Embedding Strategy

- Dense primary: `BAAI/bge-large-en-v1.5` (or multilingual variant where needed).
- Dense alternate A/B: `intfloat/e5-large-v2`, `thenlper/gte-large`.
- Instruction style for technical query/doc embedding templates.
- Sparse: SPLADE or BM25 lexical index for standards codes and exact symbols.
- Multi-vector: ColBERT-style token vectors for long technical passages.
- Batch embedding with GPU micro-batches (dynamic sizing by token count).

## 6) Retrieval Flow

1. Query preprocessor: acronym expansion, spelling normalization, unit normalization.
2. Query classifier: factual/numerical/table/diagram/cross-doc.
3. Multi-query generation (2–5 rewrites).
4. Parallel retrieval:
   - Dense ANN top-80
   - BM25 top-80
   - metadata constrained query (if user supplies doc/revision/discipline)
5. Reciprocal rank fusion → top-60.
6. Cross-encoder rerank → top-15.
7. Contextual compressor (remove redundant sentences, preserve numbers/tables).
8. Evidence validator (numeric consistency + citation presence).

## 7) Reranking Pipeline

- Stage 1: `bge-reranker-large` for semantic relevance.
- Stage 2: domain-aware cross-encoder (`cross-encoder/ms-marco-MiniLM-L-12-v2`) fine-tuned on engineering pairs.
- Score blend: `0.55*stage1 + 0.35*stage2 + 0.10*metadata_match`.
- Hard boosts: exact standard code matches, exact tag/equipment matches.

## 8) API Endpoints (FastAPI)

- `POST /v1/documents/ingest` (async job enqueue)
- `GET /v1/documents/{id}/status`
- `POST /v1/query` (single-shot QA)
- `POST /v1/chat/{session_id}/message` (memory-enabled)
- `GET /v1/citations/{answer_id}`
- `POST /v1/retrieval/debug` (returns scored chunks)
- `POST /v1/eval/run` (benchmark suite)
- `GET /v1/health/live`, `/ready`, `/metrics`

## 9) Streaming Design

- SSE for incremental answer tokens + citation events.
- Event channels:
  - `retrieval_status`
  - `draft_token`
  - `citation_append`
  - `confidence_update`
  - `final_answer`
- Backpressure with Redis streams and async generators.

## 10) Memory Architecture

- Redis for short-term conversational state (TTL sessions).
- Postgres for persistent memory snapshots (compliance/audit).
- Memory objects:
  - active topic (e.g., compressor sizing)
  - last cited docs/chunks
  - unresolved clarifications
- Retrieval uses `conversation context window summary` + `topic filter`.

## 11) Database Schema (Core)

- `documents(id, tenant_id, title, type, revision, status, source_uri, created_at)`
- `document_pages(id, document_id, page_no, ocr_text, layout_json)`
- `chunks(id, document_id, section, subsection, page_start, page_end, content, metadata_json, embedding vector)`
- `table_chunks(id, chunk_id, table_json, csv_repr, units_json)`
- `entities(id, document_id, entity_type, name, value, unit, page_no)`
- `citations(id, answer_id, chunk_id, quote_span, confidence)`
- `chat_sessions(id, tenant_id, user_id, state_json)`
- `chat_messages(id, session_id, role, content, citations_json)`

## 12) Hybrid Search Logic

- Candidate union from ANN + BM25 + filtered metadata query.
- RRF fusion with k=60.
- Enforce diversity by section/page to avoid same-page saturation.
- Apply post-filter for revision lock (e.g., latest approved revision only).

## 13) OCR Workflow

1. Detect born-digital vs scanned.
2. Scanned pages → OCR engine (PaddleOCR/Tesseract + language pack).
3. Layout detection to segment tables/figures/headers.
4. Confidence map per token; low-confidence areas flagged.
5. Human-review queue for pages below threshold.

## 14) Diagram Understanding Approach

- Extract figure crops + captions.
- Run VLM tagging for component labels (valve, exchanger, line number).
- Store diagram metadata graph:
  - nodes: equipment/instruments
  - edges: process/material/control links
- Link P&ID tag regexes (e.g., `P-101A`, `XV-2203`) to text chunks.

## 15) Hallucination Prevention Strategy

- Grounded generation prompt: answer only from supplied evidence.
- Mandatory citation checker: no citation ⇒ no final answer.
- Numeric verifier compares generated numbers against source spans.
- Confidence score from retrieval margin + rerank entropy + verifier pass/fail.
- If confidence < threshold: return
  - `Information not confidently found in document.`
  - include closest citations and clarification question.

## 16) Evaluation Metrics

- Retrieval: Recall@k, MRR, nDCG@k.
- Generation: faithfulness, answer relevancy, context precision (RAGAS).
- Numeric accuracy: exact-value match %, unit consistency %.
- Citation quality: citation precision/recall, broken citation rate.
- Ops: P95 latency, ingestion throughput, GPU utilization, error rate.

## 17) GPU Optimization Strategy

- Dedicated GPU pools by workload:
  - OCR/VLM
  - embeddings
  - reranking
  - LLM generation
- Dynamic batching and mixed precision (FP16/BF16).
- Quantized reranker/embedding models where acceptable.
- Triton or vLLM for high-throughput serving.

## 18) Deployment Architecture

- Dockerized microservices.
- Kubernetes (EKS/AKS/GKE or on-prem OpenShift).
- Helm charts for environment overlays (dev/stage/prod).
- Node pools: CPU for parsing, GPU for ML workloads.
- Blue/green deploy for API + canary for model updates.

## 19) Scaling Approach

- Horizontal scale:
  - API replicas with HPA on CPU/RPS
  - worker replicas by queue depth
  - sharded vector indexes by tenant/domain
- Caching:
  - embedding cache
  - retrieval result cache by normalized query
- Multi-region read replicas for low-latency query.

## 20) Example Engineering Queries and Answers (Style)

### Q1
**Query:** "What is the MAWP for separator V-2100 in Rev C FEED package?"

**Answer format:**
- **Fact:** MAWP for V-2100 is **125 bar(g)**.
- **Context:** Value appears in equipment design table for pressure vessel sizing.
- **Citations:** FEED_RevC.pdf, Section 4.2.1, p.20, Table 4-3, chunk `c8f1...`.

### Q2
**Query:** "Which standard governs emergency shutdown valves in this package?"

**Answer format:**
- **Fact:** ESDV requirements reference **API 14C** and project spec **PS-ESD-001**.
- **Assumption:** None.
- **Citations:** Controls_Std.pdf, Section 7.4, p.88; BOD.pdf Appendix B, p.214.

### Q3
**Query:** "List operating temperature ranges for subsea flowline FL-33 and FL-34."

**Answer format:**
- **Fact:** FL-33: **4 to 68 °C**; FL-34: **6 to 72 °C**.
- **Validation:** Units normalized to °C from source table.
- **Citations:** Subsea_DataSheet_Rev2.pdf, Section 3.6, p.47, Table 3-12.

---

## Recommended Runtime Defaults

- Chunk target: 700 tokens, overlap 120 tokens.
- Retrieve top-k: 80 dense + 80 sparse; rerank to 15.
- Confidence threshold: 0.72.
- Max context tokens to LLM: 12k.
- Retry policy: exponential backoff (3 attempts), dead-letter queue after fail.

## Security and Compliance Baseline

- SSO (OIDC/SAML), RBAC + ABAC per tenant and document classification.
- At-rest encryption: AES-256 (DB, object store, backups).
- In-transit: TLS 1.2+; mTLS internal mesh.
- Full audit trail for ingestion, retrieval, and answer generation.
- PII/secrets redaction pipeline before indexing.
