# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoreIQ RAG Service — a Python/Flask backend providing Retrieval-Augmented Generation over documents stored in PostgreSQL and MinIO. Designed as a REST API consumed by a separate Next.js frontend (not in this repo).

All application code lives under `Backend/`.

## Commands

```bash
# Install dependencies (from Backend/)
pip install -r requirements.txt

# Run development server (port 5000)
python app.py

# Production server
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 120 app:app

# Docker build and run
docker build -t coreiq-rag:latest Backend/
docker run -p 5000:5000 --env-file .env -v data:/app/data -v uploads:/app/uploads coreiq-rag:latest

# Utility scripts (from Backend/)
python scripts/initial_sync.py      # First-time document sync from databases
python scripts/rebuild_indices.py   # Rebuild FAISS and BM25 indices
python scripts/cost_report.py       # Generate token usage/cost report
```

Tests exist as empty stubs in `Backend/tests/`. No test runner is configured.

## Architecture

### Request Flow

```
JWT Auth → Flask Blueprint → Core Service → Response
```

All API routes are registered under `/api/rag/` via Flask blueprints in `Backend/api/`. Every protected endpoint uses the `@require_auth` decorator (`utils/auth.py`) which validates a JWT Bearer token and populates `g.user_id`, `g.user_email`, `g.user_name`, `g.user_role`.

### Two Primary Pipelines

**Document Ingestion** (`POST /api/rag/sync`):

```
DocumentSources (two PostgreSQL DBs) → MinIOFetcher (download files)
  → DocumentProcessor (extract PDF/TXT, chunk at 800 chars/150 overlap)
  → EmbeddingService (OpenAI text-embedding-3-small → FAISS index)
  → BM25Service (tokenize/stem → BM25 index)
  → CostTracker (log embedding token costs to DB)
```

**Query** (`POST /api/rag/search`):

```
HybridRetriever:
  Stage 1: FAISS semantic search → 20 candidates
  Stage 2: BM25 keyword search → 20 candidates
  Stage 3: Normalize + combine (0.7 semantic, 0.3 BM25) → top 15
  Stage 4: CrossEncoder rerank (ms-marco-MiniLM-L-6-v2) → top 5
→ LLMProvider (gpt-4o-mini) generates answer from top chunks
→ CostTracker logs query token costs
```

### Key Modules

| Module                          | Purpose                                                                                              |
| ------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `core/hybrid_retriever.py`      | Orchestrates FAISS + BM25 retrieval with score normalization and reranking                           |
| `core/document_sync_service.py` | Orchestrates full sync: fetch from DBs → download from MinIO → chunk → index                         |
| `core/document_sources.py`      | Fetches document metadata from main DB (`"Document"` table) and reference DB (`"GMPDocument"` table) |
| `core/embedding_service.py`     | OpenAI embedding wrapper, creates FAISS vector stores                                                |
| `core/bm25_service.py`          | BM25Okapi keyword index with NLTK preprocessing (stopwords, Porter stemming)                         |
| `core/reranker_service.py`      | CrossEncoder neural reranker, truncates to 512 chars per doc                                         |
| `core/llm_provider.py`          | Abstracts LangChain ChatOpenAI; temperature 0.0                                                      |
| `core/cost_tracker.py`          | Calculates token costs (USD→INR at 85:1), logs to `rag_token_usage` and `rag_cost_summary` tables    |
| `core/minio_fetcher.py`         | Async download from S3-compatible MinIO storage                                                      |
| `core/db.py`                    | AsyncPG per-request database connections (no pooling); two DBs: main + reference                     |
| `core/document_processor.py`    | PDF/TXT extraction via pypdf/pymupdf, chunking via RecursiveCharacterTextSplitter                    |
| `core/chat_service.py`          | Maintains conversation history (last 10 messages)                                                    |

### Data Storage

- **FAISS index**: `Backend/data/vector_stores/global/` (index.faiss, index.pkl)
- **BM25 index**: `Backend/data/bm25/global/` (bm25_index.pkl, bm25_documents.pkl, tokenized_corpus.pkl)
- **Uploads**: `Backend/uploads/`
- Both `data/` and `uploads/` are Docker volume mount points.

### Database Tables

- `rag_documents` — document metadata
- `rag_token_usage` — per-operation token/cost records (operation_type: 'query' or 'sync')
- `rag_cost_summary` — aggregated per-user cost summaries (UPSERT pattern)
- `"Document"` — SEARCH_DOC documents from admin panel (main DB)
- `"GMPDocument"` — GMP regulatory documents with product categories (reference DB)

### API Blueprints

| Blueprint    | Prefix               | File                                                       |
| ------------ | -------------------- | ---------------------------------------------------------- |
| sync_bp      | `/api/rag/`          | `api/sync.py` — sync, incremental sync, rebuild, status    |
| search_bp    | `/api/rag/`          | `api/search.py` — hybrid search, similar documents         |
| admin_bp     | `/api/rag/admin/`    | `api/admin.py` — stats, usage, costs, health               |
| documents_bp | `/api/rag/`          | `api/documents.py` — view docs, get chunks, presigned URLs |
| settings_bp  | `/api/rag/settings/` | `api/settings.py` — available models config                |

### Initialization

`app.py` creates the Flask app at module level (required for gunicorn `app:app` import). `init_services()` runs at import time: initializes DB connections, sync services, search services (loads FAISS/BM25 indices into memory), and admin services.

## Required Environment Variables

- `DATABASE_URL` — PostgreSQL connection string (main app DB)
- `REFERENCE_DATABASE_URL` — PostgreSQL connection string (reference/GMP DB)
- `OPENAI_API_KEY` — required when LLM_PROVIDER or EMBEDDING_PROVIDER is 'openai'
- `JWT_SECRET_KEY` — HS256 signing key, minimum 32 characters (shared with Next.js frontend)
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET` — MinIO/S3 storage

## Coding Conventions

- 4-space indentation throughout
- Pydantic models for request/response validation (`models/schemas.py`)
- Standardized API responses via `utils/response.py`: `success_response(data, message)` / `error_response(error, status_code)`
- Async database operations with asyncpg; Flask async route support via `Flask[async]`
- Config loaded from environment via `python-dotenv` in `config.py`
