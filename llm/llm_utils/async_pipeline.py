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
    def __init__(self, max_concurrency: int = 8, run_name: str = "batch_demo", tags = ["batching"], database: str = "clickhouse"):
        self.app = RAGApplication(name="")
        self.max_concurrency = max_concurrency
        self.run_name = run_name
        self.tags = tags
        self.database = database 
        self.run_time = time.time()
        self.config = RunnableConfig(
            max_concurrency=self.max_concurrency,
            run_name=self.run_name,
            tags=self.tags,
            metadata={"batch_size": self.max_concurrency}
        )
        self.async_runnable = RunnableLambda(lambda d: self.app.answer_question(d["question"], d["database"]))

    async def run_batch(self, questions: List[str], database: str) -> List[Any]:
        # Attach index to each input for order preservation
        indexed_inputs = [(i, {"question": q, "database": self.database}) for i, q in enumerate(questions)]
        start_time = time.time()
        completed_results = []
        print(f"Starting batch processing of {len(questions)} questions...")
        # Use a mapping from index to result
        async for (idx, result) in self._abatch_with_index(indexed_inputs):
            completed_results.append((idx, result))
            print(f"Completed question {idx + 1}/{len(questions)}: {questions[idx][:50]}...")
            if len(completed_results) % 20 == 0:
                print(f"Progress: {len(completed_results)}/{len(indexed_inputs)} completed...")
        completed_duration = time.time() - self.run_time
        self.run_time = completed_duration
        print(f"All {len(questions)} questions processed in {completed_duration:.2f} seconds")
        # Sort results by original index
        completed_results.sort(key=lambda x: x[0])
        # Return only the results, in order
        return [result for idx, result in completed_results]

    async def _abatch_with_index(self, indexed_inputs):
        # Helper generator to yield (index, result) pairs as they complete
        tasks = [self.async_runnable.abatch([inp], config=self.config) for _, inp in indexed_inputs]
        for idx, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            # abatch returns a list, so take the first element
            yield indexed_inputs[idx][0], result[0]


async def main():
    pipeline = AsyncPipeline(run_name="test-run-sri", max_concurrency=2, database="clickhouse")
    questions = ["What are the latest updates on Donald Trump?" for _ in range(3)]
    ans = await pipeline.run_batch(questions)
    print(ans)

if __name__ == "__main__":
    asyncio.run(main())
