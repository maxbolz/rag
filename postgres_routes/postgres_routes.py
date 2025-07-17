from fastapi import APIRouter, HTTPException, Query
from models.article import Article, DocumentIn
from GET import get_pg_connection
from typing import List
from pgvector.psycopg import register_vector

router = APIRouter()

@router.get("/search", response_model=List[Article])
def search_articles(question: str = Query(...), top_k: int = 5):
    # Embed and semantic search in Postgres vector DB
    pass  # Use example from previous answers

@router.post("/document")
def add_article(doc: DocumentIn):
    # Embed and insert article in Postgres
    pass


@router.get("/search/", response_model=List[Article])
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
