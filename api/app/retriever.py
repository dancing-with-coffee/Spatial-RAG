"""Spatial Hybrid Retriever for Spatial-RAG."""

import re
from dataclasses import dataclass
from typing import Any, Optional

from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim

from .config import get_settings
from .database import db
from .embeddings import embed_query
from .spatial_query import (
    build_hybrid_query,
    build_semantic_only_query,
    geojson_to_wkt,
    point_to_wkt,
)


@dataclass
class RetrievedDocument:
    """A document retrieved by the spatial hybrid retriever."""

    id: str
    title: str
    content: str
    geometry: dict[str, Any]
    geom_wkt: str
    h3_index: Optional[int]
    metadata: dict[str, Any]
    semantic_score: float
    spatial_score: Optional[float]
    spatial_distance_m: Optional[float]
    hybrid_score: Optional[float]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "geometry": self.geometry,
            "h3_index": self.h3_index,
            "metadata": self.metadata,
            "scores": {
                "semantic": (
                    round(self.semantic_score, 4) if self.semantic_score else None
                ),
                "spatial": round(self.spatial_score, 4) if self.spatial_score else None,
                "hybrid": round(self.hybrid_score, 4) if self.hybrid_score else None,
            },
            "spatial_distance_m": (
                round(self.spatial_distance_m, 2) if self.spatial_distance_m else None
            ),
        }


class SpatialHybridRetriever:
    """
    Retriever that combines semantic similarity with spatial proximity.

    Performs hybrid retrieval using:
    1. Semantic search via pgvector cosine distance
    2. Spatial filtering via PostGIS functions
    3. Hybrid scoring combining both signals
    """

    def __init__(
        self,
        alpha: float = None,
        beta: float = None,
        default_radius_m: float = None,
        top_k: int = None,
    ):
        settings = get_settings()
        self.alpha = alpha if alpha is not None else settings.hybrid_alpha
        self.beta = beta if beta is not None else settings.hybrid_beta
        self.default_radius_m = default_radius_m or settings.default_radius_m
        self.top_k = top_k or settings.retrieval_top_k

        # Initialize geocoder for location extraction
        self._geocoder = None

    @property
    def geocoder(self) -> Nominatim:
        """Lazy-load geocoder."""
        if self._geocoder is None:
            self._geocoder = Nominatim(user_agent="spatial-rag-retriever")
        return self._geocoder

    def extract_location_from_query(
        self, query: str
    ) -> Optional[tuple[float, float, str]]:
        """
        Extract location from natural language query.

        Uses simple heuristics and geocoding. For production,
        consider using an LLM for more robust extraction.

        Returns:
            Tuple of (longitude, latitude, location_name) or None
        """
        # Common location patterns
        patterns = [
            r"near\s+(.+?)(?:\?|$|,|\.|in\s)",
            r"around\s+(.+?)(?:\?|$|,|\.|in\s)",
            r"in\s+(.+?)(?:\?|$|,|\.)",
            r"at\s+(.+?)(?:\?|$|,|\.)",
            r"close to\s+(.+?)(?:\?|$|,|\.)",
            r"within\s+\d+\s*(?:m|km|meters|kilometers)\s+of\s+(.+?)(?:\?|$|,|\.)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location_text = match.group(1).strip()
                try:
                    location = self.geocoder.geocode(location_text, timeout=5)
                    if location:
                        return (location.longitude, location.latitude, location.address)
                except GeocoderTimedOut:
                    continue

        return None

    def retrieve(
        self,
        query: str,
        region_geojson: Optional[dict[str, Any]] = None,
        center_lon: Optional[float] = None,
        center_lat: Optional[float] = None,
        radius_m: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> list[RetrievedDocument]:
        """
        Retrieve documents using hybrid spatial + semantic search.

        Args:
            query: Natural language query
            region_geojson: Optional GeoJSON geometry to filter by region
            center_lon: Optional center longitude for radius search
            center_lat: Optional center latitude for radius search
            radius_m: Optional search radius in meters
            top_k: Maximum number of results

        Returns:
            List of RetrievedDocument objects ranked by hybrid score
        """
        top_k = top_k or self.top_k

        # Generate query embedding
        query_embedding = embed_query(query)

        # Convert region GeoJSON to WKT if provided
        region_wkt = None
        if region_geojson:
            region_wkt = geojson_to_wkt(region_geojson)

        # Try to extract location from query if not provided
        if not region_wkt and center_lon is None and center_lat is None:
            extracted = self.extract_location_from_query(query)
            if extracted:
                center_lon, center_lat, _ = extracted
                radius_m = radius_m or self.default_radius_m

        # Build and execute query
        has_spatial = region_wkt or (center_lon is not None and center_lat is not None)

        if has_spatial:
            sql, params = build_hybrid_query(
                query_embedding=query_embedding,
                region_wkt=region_wkt,
                center_lon=center_lon,
                center_lat=center_lat,
                radius_m=radius_m or self.default_radius_m,
                top_k=top_k,
                alpha=self.alpha,
                beta=self.beta,
            )
        else:
            # Fallback to semantic-only search
            sql, params = build_semantic_only_query(
                query_embedding=query_embedding, top_k=top_k
            )

        # Execute query
        results = db.execute_query(sql, tuple(params))

        # Convert to RetrievedDocument objects
        documents = []
        for row in results:
            doc = RetrievedDocument(
                id=str(row["id"]),
                title=row["title"],
                content=row["content"],
                geometry=row.get("geometry", {}),
                geom_wkt=row.get("geom_wkt", ""),
                h3_index=row.get("h3_index"),
                metadata=row.get("metadata", {}),
                semantic_score=float(row.get("semantic_score", 0)),
                spatial_score=(
                    float(row["spatial_score"]) if row.get("spatial_score") else None
                ),
                spatial_distance_m=(
                    float(row["spatial_distance_m"])
                    if row.get("spatial_distance_m")
                    else None
                ),
                hybrid_score=(
                    float(row["hybrid_score"]) if row.get("hybrid_score") else None
                ),
            )
            documents.append(doc)

        return documents

    def retrieve_with_context(self, query: str, **kwargs) -> dict[str, Any]:
        """
        Retrieve documents and format as context for LLM.

        Returns:
            Dict with 'documents' list and 'context_text' formatted string
        """
        documents = self.retrieve(query, **kwargs)

        # Format context for LLM
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"[Document {i}]\n"
                f"Title: {doc.title}\n"
                f"Location: {doc.geom_wkt}\n"
                f"Content: {doc.content}\n"
                f"Relevance: semantic={doc.semantic_score:.3f}"
                + (f", spatial={doc.spatial_score:.3f}" if doc.spatial_score else "")
            )

        return {
            "documents": [doc.to_dict() for doc in documents],
            "context_text": "\n\n".join(context_parts),
        }


# Singleton instance
retriever = SpatialHybridRetriever()
