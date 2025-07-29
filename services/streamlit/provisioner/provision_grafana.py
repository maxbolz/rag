import time
import requests
import json
import os

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
USERNAME = os.getenv("GRAFANA_USER", "admin")
PASSWORD = os.getenv("GRAFANA_PASS", "admin")
DASHBOARD_PATH = "dashboard.json"

# ClickHouse connection details
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "10.0.100.92")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT", "8123")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "guardian")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "user")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "default")

MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds


def wait_for_grafana(session):
    print("Waiting for Grafana to be ready...")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(f"{GRAFANA_URL}/api/health")
            if r.status_code == 200:
                print("Grafana is up.")
                return True
            else:
                print(f"Health check returned status {r.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt}: Grafana not ready ({e})")
        time.sleep(RETRY_DELAY * attempt)  # exponential backoff
    print("Failed to connect to Grafana after retries.")
    return False


def create_datasource(session):
    host = os.getenv("CLICKHOUSE_HOST")
    port = os.getenv("CLICKHOUSE_PORT")
    payload = {
        "name": "ClickHouse",
        "type": "grafana-clickhouse-datasource",
        "access": "proxy",
        "url": f"http://{host}:{port}",  # adjust in .env
        "url": f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}",
        "basicAuth": False,
        "jsonData": {
            "defaultDatabase": CLICKHOUSE_DATABASE,
            "port": int(CLICKHOUSE_PORT),
            "username": CLICKHOUSE_USER,
            "server": CLICKHOUSE_HOST,
            "secure": False,
            "protocol": "http",
            "skip-tls-verify": True
        },
        "secureJsonData": {
            "password": CLICKHOUSE_PASSWORD
        },
        "isDefault": True
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.post(f"{GRAFANA_URL}/api/datasources", json=payload)
            if r.status_code == 200:
                print("Data source created.")
                return True
            elif r.status_code == 409:
                print("Data source already exists.")
                return True
            else:
                print(f"Attempt {attempt}: Failed to create data source: {r.status_code} {r.text}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt}: Error creating data source: {e}")
        time.sleep(RETRY_DELAY * attempt)
    print("Failed to create data source after retries.")
    return False


def import_dashboard(session):
    with open(DASHBOARD_PATH, "r") as f:
        dashboard = json.load(f)

    payload = {
        "dashboard": dashboard,
        "overwrite": True,
        "folderId": 0
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.post(f"{GRAFANA_URL}/api/dashboards/db", json=payload)
            if r.status_code in (200, 202):
                print("Dashboard imported.")
                return dashboard
            else:
                print(f"Attempt {attempt}: Failed to import dashboard: {r.status_code} {r.text}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt}: Error importing dashboard: {e}")
        time.sleep(RETRY_DELAY * attempt)
    print("Failed to import dashboard after retries.")
    return None

if __name__ == "__main__":
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)

    if wait_for_grafana(session):
        if create_datasource(session):
            import_dashboard(session)

    else:
        print("Exiting due to Grafana unavailability.")
