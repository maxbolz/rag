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
    def __init__(self, max_concurrency: int = 8, run_name: str = "batch_demo", tags = ["batching"]):
        self.app = RAGApplication()
        self.max_concurrency = max_concurrency
        self.run_name = run_name
        self.tags = tags
        self.run_time = time.time()
        self.config = RunnableConfig(
            max_concurrency=self.max_concurrency,
            run_name=self.run_name,
            tags=self.tags,
            metadata={"batch_size": self.max_concurrency}
        )
        self.async_runnable = RunnableLambda(self.app.answer_question)

    async def run_batch(self, questions: List[str]) -> List[Any]:
        inputs = [{"question": q} for q in questions]
        start_time = time.time()
        completed_results = []
        async for result in self.async_runnable.abatch_as_completed(inputs, config=self.config):
            completed_results.append(result)
            # Show progress every 20 completions
            if len(completed_results) % 20 == 0:
                print(f"   📈 {len(completed_results)}/{len(inputs)} completed...")
        completed_duration = time.time() - self.run_time
        self.run_time = completed_duration
        
        return completed_results


async def main():
    pipeline = AsyncPipeline(2, "test-run-sid")
    questions = ["What are the latest protests in America?" for _ in range(3)]
    ans = await pipeline.run_batch(questions)
    print(ans)

if __name__ == "__main__":
    asyncio.run(main())
