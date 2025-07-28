import time
import requests
import json
import os

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
USERNAME = os.getenv("GRAFANA_USER", "admin")
PASSWORD = os.getenv("GRAFANA_PASS", "admin")
DASHBOARD_PATH = "dashboard.json"

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
    payload = {
        "name": "ClickHouse",
        "type": "grafana-clickhouse-datasource",
        "access": "proxy",
        "url": "http://10.0.100.92:8123",  # Adjust as needed
        "basicAuth": False,
        "jsonData": {
            "defaultDatabase": "guardian",
            "port": 8123,
            "username": "user",
            "server": "10.0.100.92",  # 👈 required
            "secure": False,
            "protocol": "http",
            "skip-tls-verify": True
        },
        "secureJsonData": {
            "password": "default"
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
