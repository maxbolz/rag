import requests
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import clickhouse_connect

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
                host=os.getenv("CLICKHOUSE_HOST"),
                port=os.getenv("CLICKHOUSE_PORT", 8123),
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
                "show-fields": "bodyText",
            }

            try:
                resp = requests.get(self.BASE, params=params)
                data = resp.json().get("response", {})
                results = data.get("results", [])

                # Filter to only include required fields
                filtered_results = []
                for article in results:
                    filtered_article = {
                        "url": article.get("webUrl"),
                        "title": article.get("webTitle"),
                        "body": article.get("fields", {}).get("bodyText"),
                        "publication_date": article.get("webPublicationDate"),
                    }
                    filtered_results.append(filtered_article)

                all_articles.extend(filtered_results)
                print(f"Fetched {len(filtered_results)} items from page {page}")

                # Safety check: stop if no data
                if not results:
                    break

            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                break

        print(f"Total articles fetched: {len(all_articles)}")
        return all_articles

    def generate_embeddings(self, articles):
        """Generate embeddings for articles"""
        embeddings = []

        for article in articles:
            # Combine title and body text for embedding
            text_for_embedding = f"{article.get('title', '')} {article.get('body', '')}"

            # Generate embedding
            embedding = self.model.encode(text_for_embedding).tolist()

            # Add embedding to article data
            article_with_embedding = {
                'url': article.get('url', ''),
                'title': article.get('title', ''),
                'body': article.get('body', ''),
                'publication_date': article.get('publication_date', ''),
                'embedding': embedding
            }
            embeddings.append(article_with_embedding)

        print(f"Generated embeddings for {len(embeddings)} articles")
        return embeddings

    def upload_to_clickhouse_debug(self, articles_with_embeddings):
        """Debug version to see data structure"""
        if self.client is None:
            print("No ClickHouse connection available")
            return False

        if not articles_with_embeddings:
            return False

        # Check first article structure
        first_article = articles_with_embeddings[0]
        print("First article keys:", list(first_article.keys()))
        print("Embedding type:", type(first_article.get('embedding')))
        print("Embedding length:", len(first_article.get('embedding', [])))

        # Try inserting just one record first
        embedding = first_article['embedding']
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()

        # Handle empty publication_date
        pub_date = first_article['publication_date']
        if not pub_date:
            pub_date = '2024-01-01T00:00:00Z'

        # Create SQL INSERT statement
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        insert_sql = f"""
        INSERT INTO guardian_articles (url, title, body, publication_date, embedding)
        VALUES (
            '{first_article['url']}',
            '{first_article['title'].replace("'", "''")}',
            '{first_article['body'].replace("'", "''")}',
            '{pub_date}',
            {embedding_str}
        )
        """

        try:
            self.client.command(insert_sql)
            print("Single record inserted successfully!")
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
    success = vectorizer.run_pipeline(page_size=10, total_needed=50)

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
