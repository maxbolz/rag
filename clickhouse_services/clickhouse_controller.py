from fastapi import FastAPI
from clickhouse_services.clickhouse_dao import ClickhouseDao
import time

app = FastAPI()

# Create controller instance
clickhouse_dao = ClickhouseDao()

@app.get("/related-articles")
async def related_articles(query: str):
    start_time = time.time()
    result = clickhouse_dao.related_articles(query)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return result


@app.post("/upload-articles")
async def upload_articles():
    start_time = time.time()
    result = clickhouse_dao.upload_articles()
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    return result