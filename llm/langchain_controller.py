import time
from fastapi import FastAPI
from pydantic import BaseModel, Field
from llm.langchain_pipeline import RAGApplication
from llm.async_pipeline import AsyncPipeline
import asyncio
from typing import List, Any, Optional
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import RunnableConfig

# Pydantic model for request body validation
class BatchQuestionRequest(BaseModel):
    query: str = Field(..., description="The question to ask")
    batch_size: Optional[int] = Field(10, description="Number of times to run the query", ge=1, le=100)
    max_workers: Optional[int] = Field(2, description="Maximum number of concurrent workers", ge=1, le=10)
    run_id: Optional[str] = Field("test-run-1", description="Unique identifier for this batch run")

# Optional: Add a route for processing different questions in a batch
class MultiBatchRequest(BaseModel):
    queries: List[str] = Field(..., description="List of questions to ask", min_items=1, max_items=50)
    max_workers: Optional[int] = Field(2, description="Maximum number of concurrent workers", ge=1, le=10)
    run_id: Optional[str] = Field("multi-batch-run", description="Unique identifier for this batch run")

class LangchainController:
    def __init__(self):
        self.app = FastAPI()
        self.pipeline = RAGApplication()
        self._register_routes()

    def _register_routes(self):
        @self.app.get("/answer-question-batch")
        async def answer_question_batch(request: BatchQuestionRequest):
            """
            Process a batch of identical questions asynchronously.
            
            Args:
                request: JSON body containing query, batch_size, max_workers, and run_id
                
            Returns:
                JSON response with answers, timing, and metadata
            """
            try:
                # Initialize async pipeline with provided parameters
                async_pipeline = AsyncPipeline(request.max_workers, request.run_id)
                
                # Track timing
                start_time = time.time()
                
                # Create batch of queries
                queries = [request.query] * request.batch_size
                
                # Run batch processing
                answers = await async_pipeline.run_batch(queries)
                
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
            
        @self.app.get("/answer-question")
        def answer_question(query: str):  # Fixed: Added proper request parameter
            """
            Process a single question.
            
            Args:
                request: JSON body containing the query
                
            Returns:
                JSON response with answer, timing, and metadata
            """
            # Track timing
            start_time = time.time()
            
            # Run single question processing
            answer = self.pipeline.answer_question(query)
            
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
        
        @self.app.get("/answer-questions-multi-batch")
        async def answer_questions_multi_batch(request: MultiBatchRequest):
            """
            Process multiple different questions asynchronously.
            
            Args:
                request: JSON body containing list of queries, max_workers, and run_id
                
            Returns:
                JSON response with answers, timing, and metadata for each query
            """
            try:
                # Initialize async pipeline
                async_pipeline = AsyncPipeline(request.max_workers, request.run_id)
                
                # Track timing
                start_time = time.time()
                
                # Run batch processing with different queries
                answers = await async_pipeline.run_batch(request.queries)
                
                end_time = time.time()
                total_duration = end_time - start_time
                
                # Pair queries with their answers
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