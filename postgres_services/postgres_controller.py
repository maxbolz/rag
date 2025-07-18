from fastapi import FastAPI
from postgres_services.postgres_dao import PostgresDao

app = FastAPI()

# Create controller instance
postgres_dao = PostgresDao()

@app.get("/related-articles")
async def related_articles(query: str):
    return postgres_dao.related_articles(query)