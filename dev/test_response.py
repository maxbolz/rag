import requests

def fetch_related_articles():
    url = "http://127.0.0.1:8000/related-articles"
    params = {"query": "epstein"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise error for bad status codes
        data = response.json()
        for content_object in data:
            print(data, end="\n\n")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except ValueError:
        print("Response content is not valid JSON.")

if __name__ == "__main__":
    fetch_related_articles()
