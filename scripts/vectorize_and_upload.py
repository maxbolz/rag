import requests
import os
import json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import clickhouse_connect
from datetime import datetime
import uuid

load_dotenv()

class GuardianVectorizer:
    def __init__(self):
        self.API_KEY = os.getenv("GUARDIAN_API_KEY")
        self.BASE = "https://content.guardianapis.com/search"
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model for embeddings
        self.client = None
        
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
    
    def create_vector_table(self):
        """Create the vector table in ClickHouse"""
        if self.client is None:
            print("No ClickHouse connection available")
            return False
            
        # Drop existing table to ensure correct schema
        try:
            self.client.command("DROP TABLE IF EXISTS guardian_articles")
            print("Dropped existing table")
        except Exception as e:
            print(f"Warning: Could not drop table: {e}")
            
        create_table_query = """
        CREATE TABLE guardian_articles (
            url String NOT NULL,
            title String NOT NULL,
            body String NOT NULL,
            publication_date DateTime64(3, 'UTC'),
            embedding Array(Float64) NOT NULL
        ) ENGINE = MergeTree()
        ORDER BY (url, publication_date)
        """
        
        try:
            self.client.command(create_table_query)
            print("Vector table created successfully")
            return True
        except Exception as e:
            print(f"Failed to create table: {e}")
            return False
    
    def fetch_articles(self, page_size=10, total_needed=50):
        """Fetch articles from Guardian API"""
        all_articles = []
        pages = (total_needed + page_size - 1) // page_size
        
        for page in range(1, pages + 1):
            params = {
                "api-key": self.API_KEY,
                "order-by": "newest",
                "page-size": page_size,
                "page": page,
                "show-fields": "all",
            }
    
            resp = requests.get(self.BASE, params=params)
            data = resp.json().get("response", {})
            results = data.get("results", [])
            all_articles.extend(results)
        print(f"Total articles fetched: {len(all_articles)}")

        return all_articles
    
    def generate_embeddings(self, articles):
        """Generate embeddings for articles"""        
        rows = []
        for article in articles:
            fields = article.get('fields', {})
            url = fields.get('shortUrl', '')
            title = fields.get('headline', '')
            body = fields.get('bodyText', '')
            publication_date = fields.get('firstPublicationDate', '2024-01-01T00:00:00Z')
            embedding = self.model.encode(body).tolist()
            row = [url, title, body, publication_date, embedding]
            rows.append(row)

        return rows
    
    def upload_to_clickhouse_debug(self, articles_with_embeddings):
        """Debug version to see data structure"""
        if self.client is None:
            print("No ClickHouse connection available")
            return False
            
        if not articles_with_embeddings:
            return False
        try:
            if articles_with_embeddings:
                print('Inserting rows into ClickHouse...')
                print(articles_with_embeddings)
                self.client.insert(
                    'guardian_articles',
                    articles_with_embeddings,
                    column_names=['url', 'title', 'body', 'publication_date', 'embedding']
                )
                return True
        except Exception as e:
            print(f"Single record failed: {e}")
            return False
       
    def search_similar_articles(self, query, limit=5):
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
            webPublicationDate,
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
    
    def run_pipeline(self, page_size=10, total_needed=50):
        """Run the complete pipeline"""
        print("Starting Guardian article vectorization pipeline...")
        
        # Connect to ClickHouse
        if not self.connect_clickhouse():
            return False
        
        # Create vector table
        if not self.create_vector_table():
            return False
        
        # Fetch articles
        articles = self.fetch_articles(page_size, total_needed)
        if not articles:
            print("No articles fetched")
            return False
        
        # Generate embeddings
        articles_with_embeddings = self.generate_embeddings(articles)
        
        # Upload to ClickHouse
        success = self.upload_to_clickhouse_debug(articles_with_embeddings)
        
        if success:
            print("Pipeline completed successfully!")
            return True
        else:
            print("Pipeline failed during upload")
            return False

def main():
    vectorizer = GuardianVectorizer()
    
    # Run the complete pipeline
    success = vectorizer.run_pipeline(page_size=100, total_needed=1000)
    
    # if success:
    #     # Test search functionality
    #     print("\nTesting search functionality...")
    #     results = vectorizer.search_similar_articles("climate change", limit=3)
        
    #     print("\nSearch results for 'climate change':")
    #     for result in results:
    #         print(f"- {result[3]} (Distance: {result[6]:.4f})")
    #         print(f"  URL: {result[1]}")
    #         print(f"  Section: {result[2]}")
    #         print()

if __name__ == "__main__":
    main() 