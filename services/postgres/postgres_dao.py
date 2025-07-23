from http.client import HTTPException

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
import os
import logging
from dotenv import load_dotenv
from scripts.pull_docs import pull_docs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()

class PostgresDao:
    def __init__(self):
        self.API_KEY = os.getenv("GUARDIAN_API_KEY")
        self.BASE = "https://content.guardianapis.com/search"
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = None
        logging.info("DAO initialized.")

    def connect_postgres(self):
        """Connect to Postgres database"""
        try:
            self.client = psycopg.connect(
                dbname=os.getenv("POSTGRES_DB", "VectorEmbeds"),
                user=os.getenv("POSTGRES_USER", "test"),
                password=os.getenv("POSTGRES_PASSWORD", "1234"),
                host=os.getenv("POSTGRES_HOST", "db"),
                port=os.getenv("POSTGRES_PORT", 5432)
            )
            logging.info("Connected to Postgres successfully.")
            print("Connected to Postgres successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to Postgres: {e}")
            print(f"Failed to connects to Postgres: {e}")
            self.client = None
            return False

    def related_articles(self, query: str, limit: int = 5):
        try:
            if not self.connect_postgres():
                raise HTTPException(500, "Failed to connect to database")
            conn = self.client
            if conn is None:
                raise HTTPException(500, "Database connection is None")
            conn.autocommit = True
            register_vector(conn)
            cur = conn.cursor()
            emb = self.model.encode(query).tolist()
            cur.execute(
                """
                SELECT url, title, body, publication_date,
                       1 - (vector <=> %s::vector) AS similarity
                FROM articles
                ORDER BY vector <=> %s::vector
                LIMIT %s
                """,
                (emb, emb, limit)
            )
            results = cur.fetchall()
            if not results:
                raise HTTPException(404, "No matches found")

            return results
            
        except Exception as e:
            logging.error(f"Exception in /search endpoint: {e}", exc_info=True)
            raise HTTPException(500, str(e))
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                conn.close()
