"""FastAPI application for Spatial-RAG."""

import json
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .config import get_settings
from .llm_generator import get_llm_generator
from .retriever import SpatialHybridRetriever

# Initialize FastAPI app
app = FastAPI(
    title="Spatial-RAG API",
    description="Spatial Retrieval Augmented Generation for geospatial reasoning",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
settings = get_settings()
retriever = SpatialHybridRetriever()


# Request/Response Models
class QueryRequest(BaseModel):
    """Request body for /query endpoint."""

    query: str = Field(..., description="Natural language query")
    region_geojson: Optional[dict[str, Any]] = Field(
        None, description="GeoJSON geometry to filter results by region"
    )
    center_lon: Optional[float] = Field(
        None, description="Center longitude for radius search"
    )
    center_lat: Optional[float] = Field(
        None, description="Center latitude for radius search"
    )
    radius_m: Optional[float] = Field(None, description="Search radius in meters")
    top_k: Optional[int] = Field(
        None, description="Maximum number of results to return"
    )
    include_answer: bool = Field(True, description="Whether to generate LLM answer")


class DocumentResponse(BaseModel):
    """Single document in query response."""

    id: str
    title: str
    content: str
    geometry: Optional[dict[str, Any]]
    metadata: Optional[dict[str, Any]]
    scores: dict[str, Optional[float]]
    spatial_distance_m: Optional[float]


class QueryResponse(BaseModel):
    """Response body for /query endpoint."""

    query: str
    answer: Optional[str]
    documents: list[DocumentResponse]
    total_count: int


# Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"service": "Spatial-RAG API", "status": "healthy", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "embedding_model": settings.embedding_model,
        "hybrid_alpha": settings.hybrid_alpha,
        "hybrid_beta": settings.hybrid_beta,
        "llm_available": bool(settings.openai_api_key),
    }


@app.post("/query", response_model=QueryResponse)
async def query_spatial_rag(request: QueryRequest):
    """
    Main Spatial-RAG query endpoint.

    Performs hybrid spatial + semantic retrieval and optionally
    generates an LLM-synthesized answer.
    """
    try:
        # Retrieve documents
        result = retriever.retrieve_with_context(
            query=request.query,
            region_geojson=request.region_geojson,
            center_lon=request.center_lon,
            center_lat=request.center_lat,
            radius_m=request.radius_m,
            top_k=request.top_k,
        )

        documents = result["documents"]
        context_text = result["context_text"]

        # Generate answer if requested and documents found
        answer = None
        if request.include_answer and documents:
            llm = get_llm_generator()
            answer = llm.generate(
                query=request.query, context_text=context_text, documents=documents
            )

        return QueryResponse(
            query=request.query,
            answer=answer,
            documents=documents,
            total_count=len(documents),
        )

    except Exception as e:
        import traceback

        error_detail = str(e)
        error_traceback = traceback.format_exc()
        print(f"Error in query_spatial_rag: {error_detail}")
        print(f"Traceback: {error_traceback}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/stream")
async def stream_query(
    q: str,
    center_lon: Optional[float] = None,
    center_lat: Optional[float] = None,
    radius_m: Optional[float] = None,
):
    """
    Streaming query endpoint using Server-Sent Events.

    Streams the LLM response in real-time as it's generated.
    """

    async def event_stream():
        try:
            # Retrieve documents
            result = retriever.retrieve_with_context(
                query=q, center_lon=center_lon, center_lat=center_lat, radius_m=radius_m
            )

            documents = result["documents"]
            context_text = result["context_text"]

            # Send metadata event
            metadata = {"doc_count": len(documents), "documents": documents}
            yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"

            # Stream LLM response
            if documents:
                llm = get_llm_generator()
                async for chunk in llm.generate_stream(
                    query=q, context_text=context_text, documents=documents
                ):
                    data = json.dumps({"chunk": chunk})
                    yield f"event: chunk\ndata: {data}\n\n"

            # Send completion event
            yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/documents")
async def list_documents(limit: int = 100, offset: int = 0):
    """List all documents in the database."""
    from .database import db

    sql = """
    SELECT 
        id, title, content, 
        ST_AsGeoJSON(geom)::json as geometry,
        h3_index, metadata, created_at
    FROM spatial_docs
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s;
    """

    results = db.execute_query(sql, (limit, offset))

    return {
        "documents": results,
        "limit": limit,
        "offset": offset,
        "count": len(results),
    }


@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get a specific document by ID."""
    from .database import db

    sql = """
    SELECT 
        id, title, content,
        ST_AsGeoJSON(geom)::json as geometry,
        ST_AsText(geom) as geom_wkt,
        h3_index, metadata, created_at
    FROM spatial_docs
    WHERE id = %s;
    """

    results = db.execute_query(sql, (doc_id,))

    if not results:
        raise HTTPException(status_code=404, detail="Document not found")

    return results[0]
