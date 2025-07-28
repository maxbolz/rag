FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY provision_grafana.py .
COPY dashboard.json .

CMD ["python", "provision_grafana.py"]