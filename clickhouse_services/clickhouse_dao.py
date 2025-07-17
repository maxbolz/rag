import clickhouse_connect
from sentence_transformers import SentenceTransformer

class ClickhouseDao:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Initialize the embedding model
        self.connect_clickhouse()

    def connect_clickhouse(self):
        """Connect to ClickHouse database"""
        try:
            self.client = clickhouse_connect.get_client(
                host='10.0.100.92',
                port=8123,
                username='user',
                password='default',
                database='guardian'
            )
            print("Connected to ClickHouse successfully")
            return True
        except Exception as e:
            print(f"Failed to connect to ClickHouse: {e}")
            self.client = None
            return False

    def related_articles(self, query: str, limit: int = 5):
        """Search for similar articles using vector similarity"""
        if self.client is None:
            print("No ClickHouse connection available")
            return []
            
        # Generate embedding for the query
        query_embedding = self.model.encode(query).tolist()
        
        # Search query using cosine similarity
        search_query = f"""
        SELECT 
            url,
            title,
            body,
            publication_date,
            cosineDistance(embedding, {query_embedding}) as distance
        FROM guardian_articles
        ORDER BY distance ASC
        LIMIT {limit}
        """
        
        try:
            result = self.client.query(search_query)
            return result.result_rows
        except Exception as e:
            print(f"Search failed: {e}")
            return []