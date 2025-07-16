from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import clickhouse_connect
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Pydantic model for the data structure
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

# ClickHouse connection configuration
def get_clickhouse_client():
    """Create and return a ClickHouse client connection"""
    try:
        client = clickhouse_connect.get_client(
            host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
            port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
            username=os.getenv('CLICKHOUSE_USERNAME', 'default'),
            password=os.getenv('CLICKHOUSE_PASSWORD', ''),
            database=os.getenv('CLICKHOUSE_DATABASE', 'default')
        )
        return client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to ClickHouse: {str(e)}")

@app.post("/documents")
async def insert_documents(data: BatchDocumentData):
    """
    Insert multiple documents into ClickHouse database
    
    Expected data format:
    {
        "documents": [
            {
                "id": "unique_id",
                "sectionname": "section_name",
                "webtitle": "web_title",
                "bodytext": "body_text_content",
                "webpublicationdate": "2024-01-01",
                "weburl": "https://example.com",
                "vector": [0.1, 0.2, 0.3, ...]
            }
        ]
    }
    """
    try:
        client = get_clickhouse_client()
        
        # Prepare data for insertion
        documents_to_insert = []
        for doc in data.documents:
            documents_to_insert.append({
                'id': doc.id,
                'sectionname': doc.sectionname,
                'webtitle': doc.webtitle,
                'bodytext': doc.bodytext,
                'webpublicationdate': doc.webpublicationdate,
                'weburl': doc.weburl,
                'vector': doc.vector
            })
        
        # Insert data into ClickHouse
        # Note: You'll need to create the table first with appropriate schema
        result = client.insert(
            table='documents',  # Replace with your actual table name
            data=documents_to_insert,
            column_names=['id', 'sectionname', 'webtitle', 'bodytext', 'webpublicationdate', 'weburl', 'vector']
        )
        
        client.close()
        
        return {
            "message": f"Successfully inserted {len(data.documents)} documents",
            "inserted_count": len(data.documents),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert documents: {str(e)}")

@app.post("/document")
async def insert_single_document(data: DocumentData):
    """
    Insert a single document into ClickHouse database
    
    Expected data format:
    {
        "id": "unique_id",
        "sectionname": "section_name",
        "webtitle": "web_title",
        "bodytext": "body_text_content",
        "webpublicationdate": "2024-01-01",
        "weburl": "https://example.com",
        "vector": [0.1, 0.2, 0.3, ...]
    }
    """
    try:
        client = get_clickhouse_client()
        
        # Prepare data for insertion
        document_data = {
            'id': data.id,
            'sectionname': data.sectionname,
            'webtitle': data.webtitle,
            'bodytext': data.bodytext,
            'webpublicationdate': data.webpublicationdate,
            'weburl': data.weburl,
            'vector': data.vector
        }
        
        # Insert data into ClickHouse
        result = client.insert(
            table='documents',  # Replace with your actual table name
            data=[document_data],
            column_names=['id', 'sectionname', 'webtitle', 'bodytext', 'webpublicationdate', 'weburl', 'vector']
        )
        
        client.close()
        
        return {
            "message": "Successfully inserted document",
            "document_id": data.id,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert document: {str(e)}")

@app.post("/create-table")
async def create_documents_table():
    """
    Create the documents table in ClickHouse if it doesn't exist
    """
    try:
        client = get_clickhouse_client()
        
        # SQL to create the table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id String,
            sectionname String,
            webtitle String,
            bodytext String,
            webpublicationdate String,
            weburl String,
            vector Array(Float32)
        ) ENGINE = MergeTree()
        ORDER BY (id, sectionname)
        """
        
        client.command(create_table_sql)
        client.close()
        
        return {
            "message": "Documents table created successfully",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create table: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
