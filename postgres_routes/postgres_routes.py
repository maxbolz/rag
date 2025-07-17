from fastapi import APIRouter, HTTPException, Query
from models.article import ArticleWithScore
from typing import List
import os
# app.py
from fastapi import FastAPI, HTTPException
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import psycopg
from fastapi import APIRouter, HTTPException, Query
import logging

# Load environment variables
load_dotenv()

app = FastAPI()

model = SentenceTransformer("all-MiniLM-L6-v2")
router = APIRouter()

def get_pg_connection():
    return psycopg.connect(
        dbname=os.getenv("POSTGRES_DB", "guardian"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
    )

@router.post("/document")
def add_article():
    # Embed and insert article in Postgres
    pass

@router.get("/search/", response_model=List[ArticleWithScore])
def search_articles(q: str, k: int = 5):
    try:
        conn = get_pg_connection()
        conn.autocommit = True
        register_vector(conn)
        cur = conn.cursor()
        emb = model.encode(q).tolist()
        cur.execute(
            """
            CREATE EXTENSION IF NOT EXISTS vector;
            SELECT url, title, body, publication_date,
                   1 - (vector <=> %s) AS similarity
            FROM articles
            ORDER BY vector <=> %s
            LIMIT %s
            """,
            (emb, emb, k)
        )
        results = cur.fetchall()
        if not results:
            raise HTTPException(404, "No matches found")
        return [
            {"url": r[0], "title": r[1], "body": r[2], "publication_date": r[3], "score": float(r[4])}
            for r in results
        ]
    except Exception as e:
        logging.error(f"Exception in /search endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))