import os
import psycopg2
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


def pull_docs(total_needed: int = 1000, page_size: int = 1):

    load_dotenv()
    API_KEY = os.getenv("GUARDIAN_API_KEY")
    BASE = "https://content.guardianapis.com/search"
    all_articles = []
    pages = total_needed // page_size

conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "guardian"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
    )

    cur = conn.cursor()

    model = SentenceTransformer("all-MiniLM-L6-v2")

    for page in range(1, pages + 1):
        params = {
            "api-key": API_KEY,
            "order-by": "newest",
            "page-size": page_size,
            "page": page,
            "show-fields": "all",
        }
        resp = requests.get(BASE, params=params)
        data = resp.json().get("response", {})
        results = data.get("results", [])
        all_articles.extend(results)
        print(f"Fetched {len(results)} items from page {page}")

        # print(results[0]['fields'])
        article = results[0]['fields']
        url = article['shortUrl']
        title = article['headline']
        body = article['bodyText']
        publication_date = article['firstPublicationDate']

        embedding = model.encode(body)
        embedding_list = embedding.tolist()

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO articles (url, title, body, publication_date, vector)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
                """,
                (url, title, body, publication_date, embedding_list)
            )
            conn.commit()

        print("Embedded: " + title)

        if not results:
            break

    conn.close()

    print(f"Total articles fetched: {len(all_articles)}")

pull_docs()

def pull_docs_stream(articles: int = 10):
    while True:
        pull_docs(articles, 1)
        time.sleep(86400)
