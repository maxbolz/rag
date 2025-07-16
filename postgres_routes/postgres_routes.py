from fastapi import APIRouter, HTTPException, Query
from models.article import Article, DocumentIn
from utils.embedding import get_embedding
from db.psql import get_psql_conn

router = APIRouter()

@router.get("/search", response_model=List[Article])
def search_articles(question: str = Query(...), top_k: int = 5):
    # Embed and semantic search in Postgres vector DB
    pass  # Use example from previous answers

@router.post("/document")
def add_article(doc: DocumentIn):
    # Embed and insert article in Postgres
    pass
