from fastapi.testclient import TestClient
from services.clickhouse.clickhouse_controller import app

# Create test client
client = TestClient(app)

def test_upload_articles():
    """Test the /upload-articles endpoint"""
    
    # Make request
    response = client.post(f"/upload-articles")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response

if __name__ == "__main__":
    test_upload_articles() 