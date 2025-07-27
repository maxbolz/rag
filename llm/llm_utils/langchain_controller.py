import time
from fastapi import FastAPI
from pydantic import BaseModel, Field
from llm_utils.langchain_pipeline import RAGApplication
from llm_utils.async_pipeline import AsyncPipeline
from typing import List, Optional


class BatchQuestionRequest(BaseModel):
    query: str = Field(...)
    batch_size: Optional[int] = Field(10, ge=1, le=100)
    max_workers: Optional[int] = Field(2, ge=1, le=10)
    run_id: Optional[str] = Field("test-run-1")
    database: Optional[str] = Field("clickhouse", description="Database to use for the query")


class MultiBatchRequest(BaseModel):
    queries: List[str] = Field(..., min_items=1, max_items=50)
    max_workers: Optional[int] = Field(2, ge=1, le=10)
    run_id: Optional[str] = Field("multi-batch-run")
    database: Optional[str] = Field("clickhouse", description="Database to use for the queries")


class LangchainController:
    def __init__(self):
        self.app = FastAPI()
        self.pipeline = RAGApplication(name="Langchain Guardian RAG Pipeline")
        self._register_routes()

    def _register_routes(self):
        @self.app.get("/answer-question")
        def answer_question(query: str, database: str):
            return self.answer_question(query, database)

        @self.app.get("/answer-question-batch")
        async def answer_question_batch(request: BatchQuestionRequest):
            return await self.answer_question_batch(request)

        @self.app.get("/answer-questions-multi-batch")
        async def answer_questions_multi_batch(request: MultiBatchRequest):
            return await self.answer_questions_multi_batch(request)

    def answer_question(self, query: str, database: str):
        start_time = time.time()
        answer = self.pipeline.answer_question(query, database)
        end_time = time.time()
        total_duration = end_time - start_time

        return {
            "status": "success",
            "query": query,
            "answer": answer,
            "total_duration": total_duration,
            "metadata": {
                "start_time": start_time,
                "end_time": end_time
            }
        }

    async def answer_question_batch(self, request: BatchQuestionRequest):
        try:
            async_pipeline = AsyncPipeline(request.max_workers, request.run_id)
            start_time = time.time()
            queries = [request.query] * request.batch_size
            answers = await async_pipeline.run_batch(queries, request.database)
            end_time = time.time()
            total_duration = end_time - start_time

            return {
                "status": "success",
                "query": request.query,
                "batch_size": request.batch_size,
                "max_workers": request.max_workers,
                "run_id": request.run_id,
                "total_duration": total_duration,
                "avg_duration_per_query": total_duration / request.batch_size,
                "answers": answers,
                "metadata": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "queries_processed": len(answers)
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "query": request.query,
                "batch_size": request.batch_size,
                "max_workers": request.max_workers,
                "run_id": request.run_id
            }

    async def answer_questions_multi_batch(self, request: MultiBatchRequest):
        try:
            async_pipeline = AsyncPipeline(request.max_workers, request.run_id)
            start_time = time.time()
            answers = await async_pipeline.run_batch(request.queries, request.database)
            end_time = time.time()
            total_duration = end_time - start_time

            results = [
                {
                    "query": query,
                    "answer": answer,
                    "index": i
                }
                for i, (query, answer) in enumerate(zip(request.queries, answers))
            ]

            return {
                "status": "success",
                "total_queries": len(request.queries),
                "max_workers": request.max_workers,
                "run_id": request.run_id,
                "total_duration": total_duration,
                "avg_duration_per_query": total_duration / len(request.queries),
                "results": results,
                "metadata": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "queries_processed": len(answers)
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "total_queries": len(request.queries),
                "max_workers": request.max_workers,
                "run_id": request.run_id
            }


controller = LangchainController()
app = controller.app
