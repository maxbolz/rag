from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from clickhouse_services.clickhouse_dao import ClickhouseDao

app = FastAPI()

class Article(BaseModel):
    url: str
    title: str
    body: str
    publication_date: datetime

# Create controller instance
clickhouse_dao = ClickhouseDao()

@app.get("/related-articles")
async def related_articles(query: str):
    return clickhouse_dao.related_articles(query)


