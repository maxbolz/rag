import time
from fastapi import FastAPI
from postgres_services.postgres_dao import PostgresDao
from scripts.pull_docs import pull_docs

app = FastAPI()

# Create controller instance
postgres_dao = PostgresDao()

@app.get("/related-articles")
async def related_articles(query: str):
    start_time = time.time()
    result =  postgres_dao.related_articles(query)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return result

@app.post("/upload-articles")
async def upload_articles():
    start_time = time.time()
    result = pull_docs()
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return result