# CLAUDE.md

## Project Identity

CoreIQ RAG Service — a production-grade Retrieval-Augmented Generation backend.

This service provides hybrid document retrieval and grounded LLM responses over documents stored in PostgreSQL and MinIO. It is consumed by a separate Next.js frontend.

All backend code resides in `Backend/`.

Primary objectives:
- Fast and reliable hybrid retrieval
- Cost-aware OpenAI usage (INR tracking)
- JWT compatibility with external frontend
- Scalable and migration-friendly architecture

---

## Current Stack

API Layer: Flask (async) + Gunicorn  
Database: PostgreSQL (asyncpg)  
Vector Search: FAISS (local disk persistence)  
Keyword Search: BM25 (NLTK-based preprocessing)  
Reranking: CrossEncoder (ms-marco-MiniLM-L-6-v2)  
LLM & Embeddings: OpenAI (gpt-4o-mini, text-embedding-3-small)  
Storage: MinIO (S3-compatible)  
Auth: JWT (HS256)  
Deployment: Docker  

---

## Core System Responsibilities

The system has two primary pipelines:

### 1. Document Ingestion
- Fetch metadata from two PostgreSQL databases
- Download files from MinIO
- Extract + chunk content (800 chars / 150 overlap)
- Generate embeddings
- Update FAISS + BM25 indices
- Track embedding token cost (USD → INR)

### 2. Query Processing
- Hybrid retrieval (semantic + keyword)
- Score normalization + weighted merge
- Optional neural reranking
- LLM answer generation using retrieved context
- Track query token cost

---

## Architectural Direction (Planned Evolution)

This system is expected to evolve toward:

- FastAPI (ASGI-native API layer)
- Qdrant (distributed vector database)
- Redis (caching, rate limiting, query optimization)
- PostgreSQL retained as primary relational store
- OpenAI retained as LLM and embedding provider
- CrossEncoder may be removed or moved to GPU inference

Improvements should prioritize:

1. Lower latency
2. Horizontal scalability
3. Memory efficiency
4. Cost efficiency
5. Backward compatibility with JWT + DB schema

Do not assume the current stack is permanent.

---

## Performance Targets

- Target query latency: < 2.5 seconds
- Moderate concurrency support (50–200 users initially)
- Avoid memory duplication across workers
- Minimize unnecessary OpenAI calls
- Retrieval quality prioritized over marginal latency gains

---

## Constraints

- Python backend required
- Must remain containerized (Docker)
- Gradual migration preferred over full rewrites
- PostgreSQL must remain system of record
- JWT contract with frontend must not break
- No Git operations allowed
- Avoid heavy dependencies unless justified by measurable gain

---

## Optimization Principles

When suggesting improvements:

- Prefer incremental optimization before architectural rewrites
- Profile bottlenecks before replacing components
- Suggest caching before model upgrades
- Avoid premature micro-optimizations
- Keep retrieval logic modular and swappable
- Avoid vendor lock-in where possible

---

## Technology Flexibility

Technology choices may change over time.

When proposing solutions:
- Favor abstraction layers over direct coupling
- Keep retrieval components modular
- Assume vector storage may migrate from FAISS to a distributed system
- Assume API layer may migrate from Flask to FastAPI

Design suggestions should not tightly bind the system to current implementations.

---

## Governance Rules

- Do not run git pull
- Do not run git fetch
- Do not run git push
- Do not access GitHub APIs
- Do not create, modify, or review PRs
- Do not trigger GitHub Actions