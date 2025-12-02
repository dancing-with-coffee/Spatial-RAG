"""Quick seeding script for Spatial-RAG database."""

import json
import math
import os
import random
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import h3
import psycopg2
from psycopg2.extras import execute_batch
from sentence_transformers import SentenceTransformer
from shapely.geometry import Point, Polygon, mapping, shape
from shapely.ops import unary_union
from shapely.wkt import dumps as wkt_dumps

# Configuration
DB_CONFIG = {
    "host": os.getenv("DATABASE_HOST", "db"),
    "port": int(os.getenv("DATABASE_PORT", 5432)),
    "database": os.getenv("DATABASE_NAME", "spatial_rag"),
    "user": os.getenv("DATABASE_USER", "postgres"),
    "password": os.getenv("DATABASE_PASSWORD", "postgres"),
}

H3_RESOLUTION = 8
BATCH_SIZE = 50


@dataclass
class SyntheticDocument:
    id: str
    title: str
    content: str
    geometry: dict[str, Any]
    metadata: dict[str, Any]


DOCUMENT_TEMPLATES = {
    "zoning": [
        "Zoning classification: {zone}. Maximum building height: {height}m. Setback: {setback}m.",
        "Land use: {zone} zone. Density: {density} units/hectare. Special: {special}.",
    ],
    "permit": [
        "Building Permit #{permit} for {project}. Completion: {date}.",
        "Development #{permit} approved. Floor area: {area} sqm.",
    ],
    "traffic": [
        "Traffic volume: {volume} vehicles/day. Congestion index: {congestion}/100.",
        "Road capacity: {capacity} vehicles/hour. Utilization: {util}%.",
    ],
    "planning": [
        "Development plan for {area}: Priority: {priority}.",
        "Master plan: {area} designated for {designation}.",
    ],
}

LANDMARKS = [
    "Central Business District",
    "University Campus",
    "Industrial Park",
    "Riverside Area",
    "Historic Quarter",
    "Tech Hub",
    "Medical Center",
    "Stadium Area",
    "Transit Station",
    "Mall District",
    "Waterfront Zone",
]

ZONES = ["R-1", "R-2", "R-3", "C-1", "C-2", "M-1", "M-2", "MU", "OS", "PD"]


def random_point(center_lat: float, center_lon: float, max_km: float = 10) -> Point:
    radius_deg = max_km / 111.0
    r = radius_deg * math.sqrt(random.random())
    theta = random.random() * 2 * math.pi
    return Point(center_lon + r * math.sin(theta), center_lat + r * math.cos(theta))


def random_polygon(
    center_lat: float, center_lon: float, max_km: float = 0.5
) -> Polygon:
    points = [
        random_point(center_lat, center_lon, max_km)
        for _ in range(random.randint(4, 7))
    ]
    hull = unary_union(points).convex_hull
    if hull.geom_type == "Polygon":
        return hull
    p = random_point(center_lat, center_lon, max_km)
    size = max_km / 111.0 * 0.3
    return Polygon(
        [
            (p.x - size, p.y - size),
            (p.x + size, p.y - size),
            (p.x + size, p.y + size),
            (p.x - size, p.y + size),
        ]
    )


def generate_content(doc_type: str, landmark: str) -> str:
    template = random.choice(
        DOCUMENT_TEMPLATES.get(doc_type, DOCUMENT_TEMPLATES["planning"])
    )
    subs = {
        "zone": random.choice(ZONES),
        "height": random.randint(10, 100),
        "setback": random.randint(3, 15),
        "density": random.randint(20, 200),
        "special": random.choice(["heritage", "flood zone", "airport zone"]),
        "permit": f"BP-{random.randint(10000, 99999)}",
        "project": random.choice(["residential", "commercial", "mixed-use"]),
        "date": (datetime.now() + timedelta(days=random.randint(180, 720))).strftime(
            "%B %Y"
        ),
        "area": random.randint(500, 50000),
        "volume": random.randint(5000, 50000),
        "congestion": random.randint(20, 95),
        "capacity": random.randint(1000, 5000),
        "util": random.randint(40, 95),
        "priority": random.choice(["housing", "transit", "green"]),
        "designation": random.choice(["growth center", "conservation", "innovation"]),
    }
    subs["area"] = landmark
    try:
        return template.format(**subs)
    except:
        return f"Document for {landmark}. Type: {doc_type}."


def generate_documents(
    n: int, center_lat: float = 31.5204, center_lon: float = 74.3587
) -> list:
    docs = []
    doc_types = list(DOCUMENT_TEMPLATES.keys())
    for i in range(n):
        doc_type = random.choice(doc_types)
        landmark = random.choice(LANDMARKS)
        geom = (
            random_polygon(center_lat, center_lon)
            if random.random() < 0.3
            else random_point(center_lat, center_lon)
        )
        days_old = random.randint(0, 1500)
        docs.append(
            SyntheticDocument(
                id=str(uuid.uuid4()),
                title=f"{doc_type.capitalize()} - {landmark} #{i+1}",
                content=generate_content(doc_type, landmark),
                geometry=mapping(geom),
                metadata={
                    "doc_type": doc_type,
                    "landmark": landmark,
                    "authority_score": round(random.uniform(0.3, 1.0), 3),
                    "recency_days": days_old,
                },
            )
        )
    return docs


def seed_database(documents: list, clear: bool = True):
    print("Loading embedding model...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    print(f"Model loaded. Dimension: {model.get_sentence_embedding_dimension()}")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    if clear:
        print("Clearing existing documents...")
        cursor.execute("DELETE FROM spatial_docs;")
        conn.commit()

    insert_sql = """
        INSERT INTO spatial_docs (id, title, content, geom, h3_index, embedding, metadata)
        VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326), %s, %s::vector, %s)
        ON CONFLICT (id) DO NOTHING;
    """

    print(f"Processing {len(documents)} documents...")
    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        contents = [f"passage: {doc.content}" for doc in batch]
        embeddings = model.encode(contents, normalize_embeddings=True)

        batch_data = []
        for doc, emb in zip(batch, embeddings):
            geom = shape(doc.geometry)
            wkt = wkt_dumps(geom, rounding_precision=6)
            centroid = geom.centroid
            h3_idx = int(h3.geo_to_h3(centroid.y, centroid.x, H3_RESOLUTION), 16)
            emb_str = f"[{','.join(map(str, emb.tolist()))}]"
            batch_data.append(
                (
                    doc.id,
                    doc.title,
                    doc.content,
                    wkt,
                    h3_idx,
                    emb_str,
                    json.dumps(doc.metadata),
                )
            )

        execute_batch(cursor, insert_sql, batch_data)
        conn.commit()
        print(f"  Processed {min(i + BATCH_SIZE, len(documents))}/{len(documents)}")

    cursor.execute("SELECT COUNT(*) FROM spatial_docs;")
    count = cursor.fetchone()[0]
    print(f"\nSeeding complete! Total documents: {count}")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    print(f"Generating {n} synthetic documents...")
    docs = generate_documents(n)
    seed_database(docs)
