import asyncio
import time
import sys
import os
from typing import List, Any
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import RunnableConfig

# Add the llm directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from langchain_pipeline import RAGApplication

app = RAGApplication()

async def test_concurrency(max_concurrency: int, num_requests: int = 10):
    """Test a specific max_concurrency value"""
    async_runnable = RunnableLambda(app.answer_question())

    config = RunnableConfig(
        max_concurrency=max_concurrency,
        run_name=f"concurrency_test_{max_concurrency}",
        tags=["concurrency_test"]
    )

    inputs = [
        {"question": "What's the latest news about technology?"} for _ in range(num_requests)
    ]

    print(f"🧪 Testing max_concurrency={max_concurrency} with {num_requests} requests...")
    start_time = time.time()
    
    completed_results = []
    errors = 0
    
    try:
        async for result in async_runnable.abatch_as_completed(inputs, config=config):
            if "Error:" in str(result.get("answer", "")):
                errors += 1
            completed_results.append(result)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return None
    
    duration = time.time() - start_time
    avg_time = duration / len(completed_results) if completed_results else 0
    
    print(f"   ✅ Completed: {len(completed_results)}/{num_requests} requests")
    print(f"   ⏱️  Total time: {duration:.2f}s")
    print(f"   📊 Avg time per request: {avg_time:.2f}s")
    print(f"   🚨 Errors: {errors}")
    print(f"   🚀 Requests/second: {len(completed_results)/duration:.2f}")
    print()
    
    return {
        "max_concurrency": max_concurrency,
        "total_time": duration,
        "avg_time": avg_time,
        "success_rate": len(completed_results)/num_requests,
        "errors": errors,
        "throughput": len(completed_results)/duration
    }

async def main():
    print("🔍 Finding optimal max_concurrency value...\n")
    
    # Test different concurrency levels
    concurrency_levels = [1, 2, 3, 5, 8, 10]
    results = []
    
    for concurrency in concurrency_levels:
        result = await test_concurrency(concurrency, num_requests=10)
        if result:
            results.append(result)
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    # Find the best performing configuration
    if results:
        best_result = max(results, key=lambda x: x["throughput"])
        print(f"🏆 Best performance: max_concurrency={best_result['max_concurrency']}")
        print(f"   Throughput: {best_result['throughput']:.2f} requests/second")
        print(f"   Avg time: {best_result['avg_time']:.2f}s per request")
        print(f"   Success rate: {best_result['success_rate']*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(main()) 