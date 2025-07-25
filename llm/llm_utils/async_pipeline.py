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
        # Attach index to each input for order preservation
        indexed_inputs = [(i, {"question": q}) for i, q in enumerate(questions)]
        start_time = time.time()
        completed_results = []
        # Use a mapping from index to result
        async for (idx, result) in self._abatch_with_index(indexed_inputs):
            completed_results.append((idx, result))
            if len(completed_results) % 20 == 0:
                print(f"   📈 {len(completed_results)}/{len(indexed_inputs)} completed...")
        completed_duration = time.time() - self.run_time
        self.run_time = completed_duration
        # Sort results by original index
        completed_results.sort(key=lambda x: x[0])
        # Return only the results, in order
        return [result for idx, result in completed_results]

    async def _abatch_with_index(self, indexed_inputs):
        # Helper generator to yield (index, result) pairs as they complete
        tasks = []
        for idx, inp in indexed_inputs:
            # Each task is a tuple of (original index, coroutine)
            task = asyncio.create_task(self.async_runnable.abatch([inp], config=self.config))
            tasks.append((idx, task))
        pending = set(task for _, task in tasks)
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for finished_task in done:
                # Find the index associated with this finished task
                idx = next(idx for idx, t in tasks if t is finished_task)
                result = await finished_task
                yield idx, result[0]


async def main():
    pipeline = AsyncPipeline(2, "test-run-sid")
    questions = ["What are the latest protests in America?" for _ in range(3)]
    ans = await pipeline.run_batch(questions)
    print(ans)

if __name__ == "__main__":
    asyncio.run(main())
