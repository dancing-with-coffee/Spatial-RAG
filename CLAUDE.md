# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spatial-RAG is a full-stack geospatial Retrieval Augmented Generation system combining semantic search (pgvector) with spatial proximity (PostGIS). The hybrid scoring formula: `score = 0.7 × semantic_similarity + 0.3 × spatial_score`.

## Commands

### Running with Docker (Recommended)
```bash
docker-compose up -d                                    # Start all services
docker exec -it spatial_rag_api python /app/seed.py 500 # Seed database with N documents
```

### Local Development
```bash
# Backend (api/)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# Frontend (frontend/)
npm install
npm run dev
```

### Linting
```bash
# Backend
flake8 api/
black --check api/

# Frontend
cd frontend && npm run lint
npx tsc --noEmit  # Type check
```

### Access Points
- Frontend: http://localhost:3000
- API Swagger docs: http://localhost:8080/docs
- PostgreSQL: localhost:5432

## Architecture

```
frontend (Next.js 14)  →  api (FastAPI)  →  db (PostGIS + pgvector)
     :3000                   :8080              :5432
```

### Backend (api/app/)
- `main.py` - FastAPI endpoints: `/query`, `/stream` (SSE), `/documents`, `/health`
- `retriever.py` - `SpatialHybridRetriever` class orchestrating hybrid search
- `spatial_query.py` - PostGIS query builders for radius/region filtering
- `embeddings.py` - BGE-small-en-v1.5 local model (384 dimensions, singleton)
- `llm_generator.py` - OpenAI streaming integration (optional, has mock fallback)
- `database.py` - Async PostgreSQL connection pool (singleton)
- `config.py` - Pydantic settings from environment

### Frontend (frontend/app/)
- `components/Map.tsx` - Leaflet map with dynamic import (avoids SSR issues)
- `components/QueryPanel.tsx` - Query form with spatial parameters
- `store/useStore.ts` - Zustand state management

### Database
- `schema.sql` - PostGIS schema with 6 indexes (GiST spatial, IVFFlat vector, GIN metadata)
- Uses H3 hierarchical indexing (resolution 8, ~460m hexagons)

## Key Patterns

- **Singleton services**: `DatabaseConnection`, `EmbeddingModel`, `LLMGenerator` - use `.get_instance()` async methods
- **BGE prefix convention**: Query embeddings use "query: " prefix, documents use "passage: " prefix
- **Streaming responses**: `/stream` endpoint uses Server-Sent Events (SSE) with event types: metadata, chunk, done, error
- **Dynamic imports**: Leaflet components use Next.js `dynamic()` with `ssr: false` to avoid window undefined errors

## Environment Variables

Required (defaults work with Docker):
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`

Optional:
- `OPENAI_API_KEY` - LLM features work without it (returns mock response)
- `HYBRID_ALPHA=0.7`, `HYBRID_BETA=0.3` - scoring weights
- `LLM_MODEL=gpt-4o-mini`, `LLM_TEMPERATURE=0.0`
