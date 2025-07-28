import time
from fastapi import FastAPI
from services.cassandra.cassandra_dao import CassandraDao
from scripts.pull_docs_cassandra import pull_docs
import logging

app = FastAPI()

# Create controller instance
cassandra_dao = CassandraDao()

@app.get("/related-articles")
async def related_articles(query: str):
    start_time = time.time()
    result =  cassandra_dao.related_articles(query)
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