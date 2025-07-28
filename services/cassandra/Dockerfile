FROM python:3.11

WORKDIR /app

RUN echo "deb https://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# Install system dependencies including PostgreSQL client libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Debug: List files in build context
RUN ls -la

# Install dependencies
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
COPY requirements.txt .
=======
COPY services/cassandra/requirements.txt .
>>>>>>> 9634c8a0ef870fa079b7b6de8463d67f3425a819
=======
COPY services/cassandra/requirements.txt .
>>>>>>> 9634c8a0ef870fa079b7b6de8463d67f3425a819
=======
COPY services/cassandra/requirements.txt .
>>>>>>> 9634c8a0ef870fa079b7b6de8463d67f3425a819
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Default command if not overridden by docker-compose
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
CMD ["python", "-m", "uvicorn", "services.cassandra.cassandra_controller:app", "--host", "0.0.0.0", "--port", "8002"]
=======
CMD ["python", "-m", "uvicorn", "services.cassandra.cassandra_controller:app", "--host", "0.0.0.0", "--port", "8003"]
>>>>>>> 9634c8a0ef870fa079b7b6de8463d67f3425a819
=======
CMD ["python", "-m", "uvicorn", "services.cassandra.cassandra_controller:app", "--host", "0.0.0.0", "--port", "8003"]
>>>>>>> 9634c8a0ef870fa079b7b6de8463d67f3425a819
=======
CMD ["python", "-m", "uvicorn", "services.cassandra.cassandra_controller:app", "--host", "0.0.0.0", "--port", "8003"]
>>>>>>> 9634c8a0ef870fa079b7b6de8463d67f3425a819
