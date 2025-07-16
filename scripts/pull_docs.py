import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GUARDIAN_API_KEY")
BASE = "https://content.guardianapis.com/search"
page_size = 1
total_needed = 1
pages = total_needed // page_size
all_articles = []

for page in range(1, 2):
    params = {
        "api-key": API_KEY,
        "order-by": "newest",
        "page-size": page_size,
        "page": page,
        "show-fields": "bodyText",
    }
    resp = requests.get(BASE, params=params)
    data = resp.json().get("response", {})
    results = data.get("results", [])
    
    # Filter to only include id, sectionName, and bodyText
    filtered_results = []
    for article in results:
        filtered_article = {
            "webUrl": article.get("webUrl"),
            "sectionName": article.get("sectionName"),
            "webTitle": article.get("webTitle"),
            "bodyText": article.get("fields", {}).get("bodyText"),
            "webPublicationDate": article.get("webPublicationDate"),
        }
        filtered_results.append(filtered_article)
    
    all_articles.extend(filtered_results)
    print(f"Fetched {len(filtered_results)} items from page {page}")

    print(filtered_results)
    # Safety check: stop if no data
    if not results:
        break

print(f"Total articles fetched: {len(all_articles)}")