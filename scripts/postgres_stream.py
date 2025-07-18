from pull_docs import pull_docs
import time
def postgres_stream(articles: int = 10):
    while True:
        pull_docs(articles, 1)
        time.sleep(86400)

postgres_stream()