from typing import List
import os
from dotenv import load_dotenvl
# app.py
from fastapi import FastAPI, HTTPException
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

app = FastAPI()

model = SentenceTransformer("all-MiniLM-L6-v2")

# Dummy embedder — replace with HuggingFace or OpenAI encoder
# need to copy this from Max's script that populates the DB with the embedded content
def embed_text(text: str) -> List[float]:
    # Example: simulate 768-dim vector
    return [0.001 * (i + 1) for i in range(768)]

# PostgreSQL connection helper
def get_pg_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "guardian"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
    )


@app.get("/search/")
def search_articles(q: str, k: int = 5):
    conn = get_pg_connection()
    conn.autocommit = True
    register_vector(conn)
    cur = conn.cursor()
    emb = model.encode(q).tolist()
    cur.execute(
        """
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

