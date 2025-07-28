import asyncio
import time
import sys
import os
from typing import List, Any, Optional
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import RunnableConfig

# Add the llm directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from langchain_pipeline import RAGApplication

class AsyncPipeline:
    def __init__(self, max_concurrency: int = 8, run_name: str = "batch_demo", database: str = "clickhouse"):
        self.app = RAGApplication(name="")
        self.max_concurrency = max_concurrency
        self.run_name = run_name
        self.tags = [database]
        self.database = database 
        self.run_time = time.time()
        self.config = RunnableConfig(
            max_concurrency=self.max_concurrency,
            run_name=self.run_name,
            tags=self.tags,
            metadata={"batch_size": self.max_concurrency}
        )
        self.async_runnable = RunnableLambda(lambda d: self.app.answer_question(d["question"], d["database"]))

    async def run_batch(self, questions: List[str]) -> List[Any]:
        start_time = time.time()
        print(f"Starting batch processing of {len(questions)} questions with database: {self.database}...")
        
        # Create inputs for each question
        inputs = [{"question": q, "database": self.database} for q in questions]
        
        # Process all questions concurrently
        results = await self.async_runnable.abatch(inputs, config=self.config)
        
        completed_duration = time.time() - start_time
        print(f"All {len(questions)} questions processed in {completed_duration:.2f} seconds")
        
        return results


async def main():
    pipeline = AsyncPipeline(run_name="test-run-sid", max_concurrency=2, database="clickhouse")
    questions = ["What are the latest updates on Epstein" for _ in range(3)]
    ans = await pipeline.run_batch(questions)
    print(ans)

if __name__ == "__main__":
    asyncio.run(main())
