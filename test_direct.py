import asyncio
from clickhouse_services.clickhouse_controller import clickhouse_dao

async def test_related_articles_direct():
    """Test the related_articles function directly"""
    
    query = "climate change"
    
    try:
        result = await clickhouse_dao.related_articles(query)
        print(f"Query: {query}")
        print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_related_articles_direct()) 