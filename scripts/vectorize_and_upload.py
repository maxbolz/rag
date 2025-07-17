import requests
import os
import json
import logging
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import clickhouse_connect
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()

class GuardianVectorizer:
    def __init__(self):
        self.API_KEY = os.getenv("GUARDIAN_API_KEY")
        self.BASE = "https://content.guardianapis.com/search"
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = None
        logging.info("GuardianVectorizer initialized.")

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
            logging.info("Connected to ClickHouse successfully.")
            print("Connected to ClickHouse successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to ClickHouse: {e}")
            print(f"Failed to connect to ClickHouse: {e}")
            self.client = None
            return False

    def create_vector_table(self):
        """Create the vector table in ClickHouse"""
        if self.client is None:
            logging.error("No ClickHouse connection available.")
            print("No ClickHouse connection available")
            return False

        try:
            self.client.command("DROP TABLE IF EXISTS guardian_articles")
            logging.info("Dropped existing table.")
            print("Dropped existing table")
        except Exception as e:
            logging.warning(f"Could not drop table: {e}")
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
            logging.info("Vector table created successfully.")
            print("Vector table created successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to create table: {e}")
            print(f"Failed to create table: {e}")
            return False

    def fetch_articles(self, page_size=10, total_needed=50):
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

    def upload_to_clickhouse_debug(self, articles_with_embeddings):
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

    def search_similar_articles(self, query, limit=5):
        """Search for similar articles using vector similarity"""
        if self.client is None:
            logging.error("No ClickHouse connection available.")
            print("No ClickHouse connection available")
            return []

        query_embedding = self.model.encode(query).tolist()
        logging.info(f"Searching for articles similar to: '{query}'")

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
            logging.info(f"Search returned {len(result.result_rows)} results.")
            return result.result_rows
        except Exception as e:
            logging.error(f"Search failed: {e}")
            print(f"Search failed: {e}")
            return []

    def run_pipeline(self, page_size=10, total_needed=50, drop=False):
        """Run the complete pipeline"""
        logging.info("Starting Guardian article vectorization pipeline...")
        print("Starting Guardian article vectorization pipeline...")

        if not self.connect_clickhouse():
            logging.error("Pipeline failed: ClickHouse connection error.")
            return False

        if drop:
            if not self.create_vector_table(drop):
                logging.error("Pipeline failed: Table creation error.")
                return False

        articles = self.fetch_articles(page_size, total_needed)
        if not articles:
            logging.error("Pipeline failed: No articles fetched.")
            print("No articles fetched")
            return False

        articles_with_embeddings = self.generate_embeddings(articles)
        success = self.upload_to_clickhouse_debug(articles_with_embeddings)

        if success:
            logging.info("Pipeline completed successfully!")
            print("Pipeline completed successfully!")
            return True
        else:
            logging.error("Pipeline failed during upload.")
            print("Pipeline failed during upload")
            return False

def main():
    vectorizer = GuardianVectorizer()
    success = vectorizer.run_pipeline(page_size=1, total_needed=10000, drop=False)
    # if success:
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