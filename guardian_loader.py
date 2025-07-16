import requests 

API_KEY = "4ffa9e47-6721-48d8-bc57-a2db4fc08902"
BASE = "https://content.guardianapis.com/search"
page_size = 200
total_needed = 10000
pages = total_needed // page_size
all_articles = []

for page in range(1, 2):
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
    print(f"{results=}")
    print(f"{data=}")

    # Safety check: stop if no data
    if not results:
        break

print(f"Total articles fetched: {len(all_articles)}")