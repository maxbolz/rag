FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY .env .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends curl

COPY ./services/clickhouse .

# This is where Uvicorn runs your FastAPI app!
CMD ["uvicorn", "clickhouse_controller:app", "--host", "0.0.0.0", "--port", "80"]