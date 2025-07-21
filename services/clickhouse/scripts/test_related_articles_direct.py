from services.clickhouse.clickhouse_controller import clickhouse_dao

def test_related_articles_direct():
    """Test the related_articles function directly"""
    
    query = "epstein"
    
    try:
        result = clickhouse_dao.related_articles(query)
        print(f"Query: {query}")
        print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_related_articles_direct() 