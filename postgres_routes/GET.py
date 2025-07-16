from fastapi import FastAPI, HTTPException, Query
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI()

# Dummy embedder — replace with HuggingFace or OpenAI encoder
# need to copy this from Max's script that populates the DB with the embedded content
def embed_text(text: str) -> List[float]:
    # Example: simulate 768-dim vector
    return [0.001 * (i + 1) for i in range(768)]

# PostgreSQL connection helper
def get_pg_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "guardian"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
    )
