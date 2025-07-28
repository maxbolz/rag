import clickhouse_connect
from sentence_transformers import SentenceTransformer
import os
import logging
import requests
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()


class Article(BaseModel):
    url: str
    title: str
    body: str
    publication_date: datetime


class ClickhouseDao:
    def __init__(self):
        self.API_KEY = os.getenv("GUARDIAN_API_KEY")
        self.BASE = "https://content.guardianapis.com/search"
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = None
        self.connect_clickhouse()
        logging.info("DAO initialized.")

    def connect_clickhouse(self):
        """Connect to ClickHouse database"""
        try:
            self.client = clickhouse_connect.get_client(
                host=os.getenv("CLICKHOUSE_HOST"),
                port=os.getenv("CLICKHOUSE_PORT", 8123),
                username='user',
                password='default',
                database='guardian'
            )
            logging.info("Connected to ClickHouse successfully.")
            print("Connected to ClickHouse successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to ClickHouse: {e}")
            print(f"Failed to connects to ClickHouse: {e}")
            self.client = None
            return False

    def fetch_guardian_articles(self, page_size=10, total_needed=50):
        """Fetch articles from Guardian API"""
        all_articles = []
        pages = (total_needed + page_size - 1) // page_size
        logging.info(f"Fetching {total_needed} articles in {pages} pages.")

        for page in range(1, pages + 1):
            params = {
                "api-key": self.API_KEY,
                "order-by": "newest",
                "page-size": page_size,
                "page": page,
                "show-fields": "all",
            }
            try:
                resp = requests.get(self.BASE, params=params)
                resp.raise_for_status()
                data = resp.json().get("response", {})
                results = data.get("results", [])
                all_articles.extend(results)
                logging.info(f"Fetched page {page}: {len(results)} articles.")
            except Exception as e:
                logging.error(f"Failed to fetch page {page}: {e}")

        logging.info(f"Total articles fetched: {len(all_articles)}")
        print(f"Total articles fetched: {len(all_articles)}")
        return all_articles

    def generate_embeddings(self, articles):
        """Generate embeddings for articles"""
        logging.info(f"Generating embeddings for {len(articles)} articles.")
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
        logging.info("Embeddings generated.")
        return rows

    def upload_to_clickhouse(self, articles_with_embeddings):
        """Debug version to see data structure"""
        if self.client is None:
            logging.error("No ClickHouse connection available.")
            print("No ClickHouse connection available")
            return False

        if not articles_with_embeddings:
            logging.warning("No articles with embeddings to upload.")
            return False
        try:
            if articles_with_embeddings:
                logging.info(f"Inserting {len(articles_with_embeddings)} rows into ClickHouse...")
                print('Inserting rows into ClickHouse...')
                self.client.insert(
                    'guardian_articles',
                    articles_with_embeddings,
                    column_names=['url', 'title', 'body', 'publication_date', 'embedding']
                )
                logging.info("Rows inserted successfully.")
                return True
        except Exception as e:
            logging.error(f"Single record failed: {e}")
            print(f"Single record failed: {e}")
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

    def upload_articles(self):
        """Run the complete pipeline to fetch, vectorize and upload Guardian articles"""
        logging.info("Starting Guardian article vectorization pipeline...")
        try:
            articles = self.fetch_guardian_articles(1, 10)
            articles_with_embeddings = self.generate_embeddings(articles)
            success = self.upload_to_clickhouse(articles_with_embeddings)
            if success:
                logging.info("Pipeline completed successfully")
                return True
            return False
        except Exception as e:
            logging.error(f"Pipeline failed: {e}")
            return False
