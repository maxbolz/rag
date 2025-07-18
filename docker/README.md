# Simple Docker Setup

## Quick Start

### 1. Set your Guardian API key
```bash
export GUARDIAN_API_KEY=your_api_key_here
```

### 2. Run everything
```bash
cd docker
docker-compose up --build
```

That's it! The database will start and the Python script will run automatically.

## What it does:
- Starts PostgreSQL with pgvector extension
- Runs your `pull_docs.py` script
- Fetches articles from Guardian API
- Stores them in the database with embeddings

## Useful commands:
```bash
# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Run just the database (for development)
docker-compose up -d db
```

## File structure:
```
docker/
├── Dockerfile          # Python app container
├── docker-compose.yml  # Orchestrates both services
├── init/
│   └── 01-schema.sql  # Database setup
└── README.md          # This file
``` 