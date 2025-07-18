FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# This is where Uvicorn runs your FastAPI app!
CMD ["uvicorn", "clickhouse_controller:app", "--host", "0.0.0.0", "--port", "80"]