import time
from fastapi import FastAPI
from postgres_services.postgres_dao import PostgresDao
from scripts.pull_docs import pull_docs
import logging

app = FastAPI()

# Create controller instance
postgres_dao = PostgresDao()

@app.get("/related-articles")
async def related_articles(query: str):
    start_time = time.time()
    result =  postgres_dao.related_articles(query)
    end_time = time.time()
    logging.info(f"GET Time taken: {end_time - start_time} seconds...you got that!")
    return result

@app.post("/upload-articles")
async def upload_articles():
    start_time = time.time()
    result = pull_docs(10)
    end_time = time.time()
    logging.info(f"POST Time taken: {end_time - start_time} seconds...you posted up!")
    return result