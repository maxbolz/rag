import os
import clickhouse_connect
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GUARDIAN_API_KEY")
BASE = "https://content.guardianapis.com/search"
page_size = 1
total_needed = 10
pages = total_needed // page_size
all_articles = []

conn = clickhouse_connect.get_client(
                host='10.0.100.92',
                port=8123,
                username='user',
                password='default',
                database='guardian'
            )


model = SentenceTransformer("all-MiniLM-L6-v2")

all_articles = []
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

rows = []
for article in all_articles[:1]:
    fields = article.get('fields', {})
    url = fields.get('shortUrl', '')
    title = fields.get('headline', '')
    body = fields.get('bodyText', '')
    publication_date = fields.get('firstPublicationDate', '')
    embedding = model.encode(body).tolist()
    row = [url, title, body, publication_date, embedding]
    rows.append(row)
    print("Embedded: " + title)

if rows:
    print('Inserting rows into ClickHouse...')
    print(rows)
    conn.insert(
        'guardian_articles',
        rows,
        column_names=['url', 'title', 'body', 'publication_date', 'embedding']
    )
conn.close()

print(f"Total articles fetched: {len(all_articles)}")