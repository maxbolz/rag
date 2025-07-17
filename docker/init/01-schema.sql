-- init/01-schema.sql

-- New schema with pgvector support
-- This creates a fresh database with proper vector types

-- Create the database
CREATE DATABASE VectorEmbeds;

-- Connect to the VectorEmbeds database
\c VectorEmbeds;

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the articles table with proper vector type
CREATE TABLE articles (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    publication_date TIMESTAMPTZ NOT NULL,
    vector vector(384)
);

-- Create an index for vector similarity search
-- CREATE INDEX ON articles USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

-- Create additional indexes for different similarity metrics
-- CREATE INDEX ON articles USING ivfflat (vector vector_l2ops) WITH (lists = 100);

-- Create a GIN index for full-text search on title and body
-- CREATE INDEX ON articles USING gin(to_tsvector('english', title || ' ' || body));

-- Verify the setup
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'articles' 
ORDER BY ordinal_position; 