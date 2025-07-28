from http.client import HTTPException

from sentence_transformers import SentenceTransformer
import os
import logging
from dotenv import load_dotenv
from cassandra.cluster import Cluster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()

class CassandraDao:
    def __init__(self):
        self.API_KEY = os.getenv("GUARDIAN_API_KEY")
        self.BASE = "https://content.guardianapis.com/search"
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = None
        logging.info("DAO initialized.")

    def connect_cassandra(self):
        """Connect to Cassandra database"""
        try:
            cassandra_host = os.getenv("CASSANDRA_HOST", "localhost")
            cassandra_port = int(os.getenv("CASSANDRA_PORT", 9042))
            cassandra_keyspace = os.getenv("CASSANDRA_KEYSPACE", "your_keyspace")

            cluster = Cluster([cassandra_host], port=cassandra_port)
            self.client = cluster.connect(cassandra_keyspace)

            logging.info("Connected to Cassandra successfully.")
            print("Connected to Cassandra successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to Cassandra: {e}")
            print(f"Failed to connects to Cassandra: {e}")
            self.client = None
            return False

    def related_articles(self, query: str, limit: int = 5):
        try:
            if not self.connect_cassandra():
                raise HTTPException(500, "Failed to connect to database")
            conn = self.client
            if conn is None:
                raise HTTPException(500, "Database connection is None")

            emb = self.model.encode(query).tolist()

            query_cql = """
                SELECT url, title, body, publication_date
                FROM articles
                ORDER BY vector ANN OF ?
                LIMIT ?
            """

            prepared = self.client.prepare(query_cql)
            rows = self.client.execute(prepared, (emb, limit))

            results = [(row.url, row.title, row.body, row.publication_date, "No Similarity Score") for row in rows]

            if not results:
                raise HTTPException(404, "No matches found")

            return results

        except Exception as e:
            logging.error(f"Exception in /search endpoint: {e}", exc_info=True)
            raise HTTPException(500, str(e))
