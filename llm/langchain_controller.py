import time
from fastapi import FastAPI
from llm.langchain_pipeline import RAGApplication
from llm.async_pipeline import AsyncPipeline
import asyncio
from typing import List, Any
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import RunnableConfig

app = FastAPI()

@app.get("/answer-question")
async def answer_question(query: str):
    async_pipeline = AsyncPipeline(2, "test-run-1")
    start_time = time.time()
    completed_duration = time.time() - start_time
    answer = await async_pipeline.run_batch([query] * 10)
    end_time = time.time()
    return answer
