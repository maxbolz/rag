FROM python:3.11-slim

WORKDIR /app

# Copy the local requirements.txt from the clickhouse service directory
COPY services/clickhouse/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the clickhouse service files
COPY services/clickhouse/ .

# This is where Uvicorn runs your FastAPI app!
CMD ["uvicorn", "clickhouse_controller:app", "--host", "0.0.0.0", "--port", "80"]