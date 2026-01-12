-- schema.sql
-- Initialize PostGIS and pgvector extensions, create tables for Spatial-RAG

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Main table for spatial documents
CREATE TABLE IF NOT EXISTS spatial_docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    geom GEOMETRY(Geometry, 4326),
    h3_index BIGINT,
    embedding VECTOR(768),  -- google/embeddinggemma-300m outputs 768 dimensions
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Spatial index using GiST for fast geographic queries
CREATE INDEX IF NOT EXISTS idx_spatial_docs_geom 
ON spatial_docs USING GIST (geom);

-- H3 index for coarse spatial bucketing
CREATE INDEX IF NOT EXISTS idx_spatial_docs_h3 
ON spatial_docs (h3_index);

-- Vector index using IVFFlat for approximate nearest neighbor search
-- Lists parameter should be sqrt(n) where n is expected row count
-- For ~1000 docs, lists=32 is reasonable; increase for larger datasets
CREATE INDEX IF NOT EXISTS idx_spatial_docs_embedding 
ON spatial_docs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 32);

-- Index on created_at for recency-based queries
CREATE INDEX IF NOT EXISTS idx_spatial_docs_created_at 
ON spatial_docs (created_at DESC);

-- GIN index on metadata for JSONB queries
CREATE INDEX IF NOT EXISTS idx_spatial_docs_metadata 
ON spatial_docs USING GIN (metadata);

-- Table for storing reranker training data (optional, for learned reranking)
CREATE TABLE IF NOT EXISTS reranker_training (
    id SERIAL PRIMARY KEY,
    doc_id UUID REFERENCES spatial_docs(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    semantic_score FLOAT,
    spatial_distance_m FLOAT,
    recency_days INTEGER,
    authority_score FLOAT,
    label INTEGER CHECK (label IN (0, 1)),  -- 1 = relevant, 0 = not relevant
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reranker_doc_id 
ON reranker_training (doc_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_spatial_docs_updated_at ON spatial_docs;
CREATE TRIGGER update_spatial_docs_updated_at
    BEFORE UPDATE ON spatial_docs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Helper function to compute hybrid score in SQL
CREATE OR REPLACE FUNCTION hybrid_score(
    semantic_dist FLOAT,
    spatial_dist_m FLOAT,
    alpha FLOAT DEFAULT 0.7,
    beta FLOAT DEFAULT 0.3
) RETURNS FLOAT AS $$
BEGIN
    RETURN alpha * (1.0 - semantic_dist) + beta * (1.0 / (1.0 + COALESCE(spatial_dist_m, 1000000)));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

