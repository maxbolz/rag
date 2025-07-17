from fastapi import FastAPI
from clickhouse_services.clickhouse_dao import ClickhouseDao

app = FastAPI()

# Create controller instance
clickhouse_dao = ClickhouseDao()

@app.get("/related-articles")
async def related_articles(query: str):
    return clickhouse_dao.related_articles(query)


@app.post("/upload-articles")
async def upload_articles():
    return clickhouse_dao.upload_articles()