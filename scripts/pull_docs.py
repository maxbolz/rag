import os
import psycopg
import logging
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def pull_docs(total_needed: int = 1000, page_size: int = 1):

    load_dotenv()
    API_KEY = os.getenv("GUARDIAN_API_KEY")
    BASE = "https://content.guardianapis.com/search"
    all_articles = []
    pages = total_needed // page_size
    
    logging.info(f"Starting to fetch {total_needed} articles with page_size={page_size}")
    logging.info(f"API Key present: {'Yes' if API_KEY else 'No'}")

    conn = psycopg.connect(
            dbname=os.getenv("POSTGRES_DB", "VectorEmbeds"),
            user=os.getenv("POSTGRES_USER", "test"),
            password=os.getenv("POSTGRES_PASSWORD", "1234"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", 5430),
        )

    model = SentenceTransformer("all-MiniLM-L6-v2")
    articles_inserted = 0
    articles_skipped = 0
    
    try:
        for page in range(1, pages + 1):
            params = {
                "api-key": API_KEY,
                "order-by": "newest",
                "page-size": page_size,
                "page": page,  # Offset to fetch older articles (skip recent 2000 pages)
                "show-fields": "all",
            }
            
            logging.info(f"--- Fetching page {page} ---")
            logging.debug(f"Request URL: {BASE}")
            
            resp = requests.get(BASE, params=params)
            
            data = resp.json().get("response", {})
            results = data.get("results", [])
            all_articles.extend(results)
            
            logging.info(f"Fetched {len(results)} items from page {page}")
            
            if not results:
                logging.warning("No results returned, stopping...")
                break

            # Process each article
            for i, result in enumerate(results):
                article = result['fields']
                url = article['shortUrl']
                title = article['headline']
                body = article['bodyText']
                publication_date = article['firstPublicationDate']
                
                logging.info(f"  Title: {title[:100]}...")

                embedding = model.encode(body)
                embedding_list = embedding.tolist()

                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO articles (url, title, body, publication_date, vector)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                        RETURNING url;
                        """,
                        (url, title, body, publication_date, embedding_list)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    
                    if result:
                        articles_inserted += 1
                        logging.info(f"  ✅ INSERTED: {title[:50]}...")
                    else:
                        articles_skipped += 1
                        logging.info(f"  ⏭️  SKIPPED (duplicate): {title[:50]}...")

            logging.info(f"Page {page} summary: {articles_inserted} inserted, {articles_skipped} skipped")

        conn.close()

        logging.info("=== FINAL SUMMARY ===")
        logging.info(f"Articles inserted: {articles_inserted}")
        logging.info(f"Articles skipped (duplicates): {articles_skipped}")
        logging.info(f"Total processed: {articles_inserted + articles_skipped}")

        return True
    except Exception as e:
        logging.error(f"❌ Pipeline failed: {e}")
        return False