from fastapi.testclient import TestClient
from services.clickhouse.clickhouse_controller import app

# Create test client
client = TestClient(app)

def test_related_articles():
    """Test the /related-articles endpoint"""
    
    # Test query
    query = "epstein"
    
    # Make request
    response = client.get(f"/related-articles?query={query}")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response

if __name__ == "__main__":
    test_related_articles() 