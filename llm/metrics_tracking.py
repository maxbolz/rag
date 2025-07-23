import asyncio
import time
from typing import List, Any
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import RunnableConfig
from langchain_pipeline import RAGApplication

app = RAGApplication()

async def main():
    async_runnable = RunnableLambda(app.answer_question())

    config = RunnableConfig(
        max_concurrency=10,  # Limit parallel execution to 10 concurrent calls
        run_name="batch_demo",
        tags=["batching", "demo"],
        metadata={"batch_size": 3}
    )

    inputs = [
        {"question": "What is the capital of France?"},
        {"question": "What is the capital of Germany?"},
        {"question": "What is the capital of Italy?"},
        {"question": "What is the capital of Spain?"},
        {"question": "What is the capital of Portugal?"},
    ]

    print("🏃 Method 3: Asynchronous abatch_as_completed()")
    start_time = time.time()
    
    completed_results = []
    async for result in async_runnable.abatch_as_completed(inputs, config=config):
        completed_results.append(result)
        # Show progress every 20 completions
        if len(completed_results) % 20 == 0:
            print(f"   📈 {len(completed_results)}/100 completed...")
    
    completed_duration = time.time() - start_time
    print(f"✅ Batch as completed finished in {completed_duration:.2f} seconds")
    
    print()

if __name__ == "__main__":
    asyncio.run(main())
