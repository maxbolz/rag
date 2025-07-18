FROM python:3.11-slim

WORKDIR /app

# Debug: List files in build context
RUN ls -la

# Install dependencies (commented out for now)
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install psycopg
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Default command if not overridden by docker-compose

# This is where Uvicorn runs your FastAPI app!
CMD ["uvicorn", "postgres_services.postgres_controller:app", "--host", "0.0.0.0", "--port", "80"]