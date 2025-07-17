-- init/01-schema.sql

CREATE DATABASE VectorEmbeds;
CREATE TABLE articles (
	url TEXT PRIMARY KEY,
	title TEXT NOT NULL,
	body TEXT NOT NULL,
	publication_date TIMESTAMPTZ NOT NULL,
	vector FLOAT8[] NOT NULL
)