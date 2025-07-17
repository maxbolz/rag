from pydantic import BaseModel
from datetime import datetime
from typing import List

class Article(BaseModel):
    url: str
    title: str
    body: str
    publication_date: datetime

class ArticleWithScore(Article):
    score: float

# Example: @app.get("/articles/search", response_model=List[ArticleWithScore])
