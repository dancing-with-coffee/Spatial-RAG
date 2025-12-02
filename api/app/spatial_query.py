"""Spatial query utilities for PostGIS."""

import json
from typing import Any, Optional

from shapely.geometry import Point, Polygon, mapping, shape
from shapely.validation import make_valid
from shapely.wkt import dumps as wkt_dumps
from shapely.wkt import loads as wkt_loads


def geojson_to_wkt(geojson_geom: dict[str, Any]) -> str:
    """
    Convert GeoJSON geometry to WKT string.

    Args:
        geojson_geom: GeoJSON geometry object (dict with type and coordinates)

    Returns:
        WKT string representation

    Raises:
        ValueError: If geometry is invalid or empty
    """
    if not geojson_geom:
        raise ValueError("Empty geometry")

    geom = shape(geojson_geom)
    if not geom.is_valid:
        geom = make_valid(geom)

    return wkt_dumps(geom, rounding_precision=6)


def wkt_to_geojson(wkt_str: str) -> dict[str, Any]:
    """
    Convert WKT string to GeoJSON geometry.

    Args:
        wkt_str: WKT string representation

    Returns:
        GeoJSON geometry object
    """
    geom = wkt_loads(wkt_str)
    return mapping(geom)


def point_to_wkt(lon: float, lat: float) -> str:
    """Create WKT POINT from coordinates."""
    return f"POINT({lon} {lat})"


def build_spatial_filter(
    region_wkt: Optional[str] = None,
    center_lon: Optional[float] = None,
    center_lat: Optional[float] = None,
    radius_m: Optional[float] = None,
    srid: int = 4326,
) -> tuple[str, list[Any]]:
    """
    Build SQL WHERE clause for spatial filtering.

    Supports two modes:
    1. Region filter: ST_Intersects with provided polygon/region WKT
    2. Radius filter: ST_DWithin from center point

    Args:
        region_wkt: WKT of region polygon for intersection filter
        center_lon: Longitude of center point for radius filter
        center_lat: Latitude of center point for radius filter
        radius_m: Search radius in meters (used with center point)
        srid: Spatial reference ID (default 4326 = WGS84)

    Returns:
        Tuple of (SQL clause string, list of parameters)
    """
    if region_wkt:
        # Region intersection filter
        sql = "ST_Intersects(geom, ST_GeomFromText(%s, %s))"
        params = [region_wkt, srid]
        return sql, params

    if center_lon is not None and center_lat is not None and radius_m:
        # Radius filter using geography for accurate meter distances
        sql = """ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_Point(%s, %s), %s)::geography,
            %s
        )"""
        params = [center_lon, center_lat, srid, radius_m]
        return sql, params

    # No spatial filter
    return "TRUE", []


def build_hybrid_query(
    query_embedding: list[float],
    region_wkt: Optional[str] = None,
    center_lon: Optional[float] = None,
    center_lat: Optional[float] = None,
    radius_m: Optional[float] = None,
    top_k: int = 50,
    alpha: float = 0.7,
    beta: float = 0.3,
) -> tuple[str, list[Any]]:
    """
    Build hybrid spatial + semantic SQL query.

    Returns documents ranked by:
    score = alpha * semantic_similarity + beta * spatial_score

    Args:
        query_embedding: Query vector for semantic similarity
        region_wkt: Optional WKT region for spatial filtering
        center_lon: Optional center longitude for distance calculation
        center_lat: Optional center latitude for distance calculation
        radius_m: Optional search radius in meters
        top_k: Maximum results to return
        alpha: Weight for semantic similarity (default 0.7)
        beta: Weight for spatial proximity (default 0.3)

    Returns:
        Tuple of (SQL query string, list of parameters)
    """
    params = []

    # Build spatial filter
    spatial_filter, spatial_params = build_spatial_filter(
        region_wkt=region_wkt,
        center_lon=center_lon,
        center_lat=center_lat,
        radius_m=radius_m,
    )

    # Determine reference point for distance calculation
    if center_lon is not None and center_lat is not None:
        ref_point = f"ST_SetSRID(ST_Point({center_lon}, {center_lat}), 4326)"
    elif region_wkt:
        ref_point = f"ST_Centroid(ST_GeomFromText('{region_wkt}', 4326))"
    else:
        ref_point = "geom"  # Self-reference (distance will be 0)

    # Build query with hybrid scoring
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    sql = f"""
    SELECT 
        id,
        title,
        content,
        ST_AsText(geom) as geom_wkt,
        ST_AsGeoJSON(geom)::json as geometry,
        h3_index,
        metadata,
        created_at,
        (embedding <=> %s::vector) as semantic_distance,
        ST_Distance(geom::geography, {ref_point}::geography) as spatial_distance_m,
        (1 - (embedding <=> %s::vector)) as semantic_score,
        (1.0 / (1.0 + COALESCE(ST_Distance(geom::geography, {ref_point}::geography), 1000000))) as spatial_score,
        hybrid_score(
            (embedding <=> %s::vector),
            ST_Distance(geom::geography, {ref_point}::geography),
            %s,
            %s
        ) as hybrid_score
    FROM spatial_docs
    WHERE {spatial_filter}
    ORDER BY hybrid_score DESC
    LIMIT %s;
    """

    params = [
        embedding_str,  # For semantic_distance
        embedding_str,  # For semantic_score
        embedding_str,  # For hybrid_score
        alpha,
        beta,
        *spatial_params,
        top_k,
    ]

    return sql, params


def build_semantic_only_query(
    query_embedding: list[float], top_k: int = 50
) -> tuple[str, list[Any]]:
    """
    Build semantic-only query (no spatial filtering).

    Useful for queries without location context.
    """
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    sql = """
    SELECT 
        id,
        title,
        content,
        ST_AsText(geom) as geom_wkt,
        ST_AsGeoJSON(geom)::json as geometry,
        h3_index,
        metadata,
        created_at,
        (embedding <=> %s::vector) as semantic_distance,
        (1 - (embedding <=> %s::vector)) as semantic_score
    FROM spatial_docs
    ORDER BY semantic_distance ASC
    LIMIT %s;
    """

    params = [embedding_str, embedding_str, top_k]
    return sql, params
