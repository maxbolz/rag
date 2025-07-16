from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Pydantic models
class DocumentData(BaseModel):
    id: str
    sectionname: str
    webtitle: str
    bodytext: str
    webpublicationdate: str
    weburl: str
    vector: List[float]

class BatchDocumentData(BaseModel):
    documents: List[DocumentData]

def get_postgres_conn():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB', 'your_db'),
            user=os.getenv('POSTGRES_USER', 'your_user'),
            password=os.getenv('POSTGRES_PASSWORD', ''),
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to PostgreSQL: {str(e)}")

@app.post("/create-table")
async def create_documents_table():
    """
    Create the documents table in PostgreSQL if it doesn't exist.
    Requires pgvector installed: https://github.com/pgvector/pgvector
    """
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            sectionname TEXT,
            webtitle TEXT,
            bodytext TEXT,
            webpublicationdate TEXT,
            weburl TEXT,
            vector vector(768)  -- Adjust the dimension to match your embedding size
        );
    """
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(create_table_sql)
        conn.commit()
        cur.close()
        return {"message": "Documents table created successfully", "status": "success"}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create table: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.post("/documents")
async def insert_documents(data: BatchDocumentData):
    """
    Insert multiple documents into PostgreSQL database.
    """
    insert_sql = """
        INSERT INTO documents (id, sectionname, webtitle, bodytext, webpublicationdate, weburl, vector)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            sectionname=EXCLUDED.sectionname,
            webtitle=EXCLUDED.webtitle,
            bodytext=EXCLUDED.bodytext,
            webpublicationdate=EXCLUDED.webpublicationdate,
            weburl=EXCLUDED.weburl,
            vector=EXCLUDED.vector;
    """
    records = [
        (
            doc.id,
            doc.sectionname,
            doc.webtitle,
            doc.bodytext,
            doc.webpublicationdate,
            doc.weburl,
            doc.vector
        ) for doc in data.documents
    ]
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()
        execute_values(cur, insert_sql, records)
        conn.commit()
        cur.close()
        return {
            "message": f"Successfully inserted {len(data.documents)} documents",
            "inserted_count": len(data.documents),
            "status": "success"
        }
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to insert documents: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.post("/document")
async def insert_single_document(data: DocumentData):
    """
    Insert a single document into PostgreSQL database.
    """
    insert_sql = """
        INSERT INTO documents (id, sectionname, webtitle, bodytext, webpublicationdate, weburl, vector)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            sectionname=EXCLUDED.sectionname,
            webtitle=EXCLUDED.webtitle,
            bodytext=EXCLUDED.bodytext,
            webpublicationdate=EXCLUDED.webpublicationdate,
            weburl=EXCLUDED.weburl,
            vector=EXCLUDED.vector;
    """
    values = (
        data.id,
        data.sectionname,
        data.webtitle,
        data.bodytext,
        data.webpublicationdate,
        data.weburl,
        data.vector
    )
    conn = None
    try:
        conn = get_postgres_conn()
        cur = conn.cursor()
        cur.execute(insert_sql, values)
        conn.commit()
        cur.close()
        return {
            "message": "Successfully inserted document",
            "document_id": data.id,
            "status": "success"
        }
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to insert document: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
