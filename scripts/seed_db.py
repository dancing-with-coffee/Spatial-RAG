"""
Database Seeding Script for Spatial-RAG.

Loads synthetic documents into PostGIS with:
- H3 spatial indexing
- BGE embeddings via local model
- Batch processing for efficiency
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json

import h3
import psycopg2
from psycopg2.extras import execute_batch
from shapely.geometry import shape
from shapely.wkt import dumps as wkt_dumps
from tqdm import tqdm

from scripts.synthetic_data import SyntheticDocument, generate_synthetic_documents

# Configuration
DB_CONFIG = {
    "host": os.getenv("DATABASE_HOST", "localhost"),
    "port": int(os.getenv("DATABASE_PORT", 5432)),
    "database": os.getenv("DATABASE_NAME", "spatial_rag"),
    "user": os.getenv("DATABASE_USER", "postgres"),
    "password": os.getenv("DATABASE_PASSWORD", "postgres"),
}

H3_RESOLUTION = 8  # ~460m hexagon edge length
BATCH_SIZE = 50


def get_embedding_model():
    """Load the BGE embedding model."""
    from sentence_transformers import SentenceTransformer

    print("Loading embedding model: BAAI/bge-small-en-v1.5")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    print(f"Model loaded. Dimension: {model.get_sentence_embedding_dimension()}")
    return model


def compute_h3_index(geometry: dict) -> int:
    """Compute H3 index from GeoJSON geometry."""
    geom = shape(geometry)
    centroid = geom.centroid
    h3_cell = h3.geo_to_h3(centroid.y, centroid.x, H3_RESOLUTION)
    # Convert hex string to integer for storage
    return int(h3_cell, 16)


def format_embedding(embedding: list[float]) -> str:
    """Format embedding as PostgreSQL vector string."""
    return f"[{','.join(map(str, embedding))}]"


def seed_database(
    documents: list[SyntheticDocument],
    batch_size: int = BATCH_SIZE,
    clear_existing: bool = False,
):
    """
    Seed the database with synthetic documents.

    Args:
        documents: List of SyntheticDocument objects
        batch_size: Number of documents to process in each batch
        clear_existing: Whether to clear existing documents first
    """
    # Load embedding model
    model = get_embedding_model()

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        if clear_existing:
            print("Clearing existing documents...")
            cursor.execute("DELETE FROM spatial_docs;")
            conn.commit()

        # SQL for inserting documents
        insert_sql = """
            INSERT INTO spatial_docs (id, title, content, geom, h3_index, embedding, metadata)
            VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326), %s, %s::vector, %s)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                geom = EXCLUDED.geom,
                h3_index = EXCLUDED.h3_index,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata;
        """

        print(f"Processing {len(documents)} documents in batches of {batch_size}...")

        total_batches = (len(documents) + batch_size - 1) // batch_size

        for batch_start in tqdm(
            range(0, len(documents), batch_size), total=total_batches
        ):
            batch = documents[batch_start : batch_start + batch_size]

            # Generate embeddings for batch
            contents = [f"passage: {doc.content}" for doc in batch]
            embeddings = model.encode(contents, normalize_embeddings=True)

            # Prepare batch data
            batch_data = []
            for doc, embedding in zip(batch, embeddings):
                geom = shape(doc.geometry)
                wkt = wkt_dumps(geom, rounding_precision=6)
                h3_idx = compute_h3_index(doc.geometry)
                embedding_str = format_embedding(embedding.tolist())

                batch_data.append(
                    (
                        doc.id,
                        doc.title,
                        doc.content,
                        wkt,
                        h3_idx,
                        embedding_str,
                        json.dumps(doc.metadata),
                    )
                )

            # Execute batch insert
            execute_batch(cursor, insert_sql, batch_data)
            conn.commit()

        # Get final count
        cursor.execute("SELECT COUNT(*) FROM spatial_docs;")
        count = cursor.fetchone()[0]
        print(f"\nSeeding complete! Total documents in database: {count}")

    except Exception as e:
        conn.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def verify_database():
    """Verify the database has been seeded correctly."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Check document count
        cursor.execute("SELECT COUNT(*) FROM spatial_docs;")
        count = cursor.fetchone()[0]
        print(f"Total documents: {count}")

        # Check geometry types
        cursor.execute(
            """
            SELECT ST_GeometryType(geom), COUNT(*) 
            FROM spatial_docs 
            GROUP BY ST_GeometryType(geom);
        """
        )
        print("\nGeometry types:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")

        # Check document types from metadata
        cursor.execute(
            """
            SELECT metadata->>'doc_type', COUNT(*) 
            FROM spatial_docs 
            GROUP BY metadata->>'doc_type';
        """
        )
        print("\nDocument types:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")

        # Sample spatial query test
        cursor.execute(
            """
            SELECT title, ST_AsText(geom), metadata->>'doc_type'
            FROM spatial_docs
            LIMIT 3;
        """
        )
        print("\nSample documents:")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[2]})")
            print(f"    Location: {row[1][:50]}...")

        return True

    except Exception as e:
        print(f"Verification error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed Spatial-RAG database with synthetic documents"
    )
    parser.add_argument(
        "-n",
        "--num-docs",
        type=int,
        default=1000,
        help="Number of documents to generate",
    )
    parser.add_argument(
        "--clear", action="store_true", help="Clear existing documents before seeding"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing data, don't seed",
    )
    parser.add_argument("--lat", type=float, default=31.5204, help="Center latitude")
    parser.add_argument("--lon", type=float, default=74.3587, help="Center longitude")
    parser.add_argument("--city", type=str, default="Lahore", help="City name")

    args = parser.parse_args()

    if args.verify_only:
        print("Verifying database...")
        verify_database()
    else:
        print(f"Generating {args.num_docs} synthetic documents...")
        docs = generate_synthetic_documents(
            n=args.num_docs, center_lat=args.lat, center_lon=args.lon, city=args.city
        )

        print(f"Seeding database...")
        seed_database(docs, clear_existing=args.clear)

        print("\nVerifying database...")
        verify_database()
