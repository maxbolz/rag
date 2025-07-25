-- Keyspace: like a database in PostgreSQL
CREATE KEYSPACE IF NOT EXISTS vectorembeds
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Use the keyspace
USE vectorembeds;

-- Create the articles table
CREATE TABLE IF NOT EXISTS articles (
    url TEXT PRIMARY KEY,
    title TEXT,
    body TEXT,
    publication_date TIMESTAMP,
    vector VECTOR<FLOAT, 384>
);

CREATE CUSTOM INDEX IF NOT EXISTS ann_index ON articles(vector)
    USING 'StorageAttachedIndex';