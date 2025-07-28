```
░█████████     ░███      ░██████     ░███████   ░████████              
░██     ░██   ░██░██    ░██   ░██    ░██   ░██  ░██    ░██             
░██     ░██  ░██  ░██  ░██           ░██    ░██ ░██    ░██   ░███████  
░█████████  ░█████████ ░██  █████    ░██    ░██ ░████████   ░██        
░██   ░██   ░██    ░██ ░██     ██    ░██    ░██ ░██     ░██  ░███████  
░██    ░██  ░██    ░██  ░██  ░███    ░██   ░██  ░██     ░██        ░██ 
░██     ░██ ░██    ░██   ░█████░█    ░███████   ░█████████   ░███████  
```

# Usage

This repository can be used to measure the metrics of various vector databases.

# Setup

1. Get a Guardian API key [here](https://bonobo.capi.gutools.co.uk/register/developer).

2. Create a `.env` file at the project root in the same directory as the `.git` folder with the following fields:

```
# PostgreSQL
POSTGRES_DB="guardian"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="<your-password>"
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432

# Clickhouse 
CLICKHOUSE_DB=guardian
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD="<your-password>"

GUARDIAN_API_KEY="<your-key>"

<<<<<<< HEAD
HOST="localhost" or shared IP address holding the container 
=======
ANTHROPIC_API_KEY="<your-key>"
LANGSMITH_TRACING="true"
LANGSMITH_API_KEY="<your-key>"

DATABASE_TYPE="<name of database>"
HOST="localhost" or shared IPv4 address 
>>>>>>> 9634c8a0ef870fa079b7b6de8463d67f3425a819
```

3. Install PostgreSQL; ensure you **write down your login somewhere safe**.

4. build Docker image for PostgreSQL using 'docker-compose build --no-cache"

5. Run Docker for PostgreSQL using `docker-compose up`

6. When done, close Docker using `docker-compose down`

# Running

## Mac

In working directory, run 
```chmod +x run.sh && ./run.sh```.

## Windows

Run `run.bat`.

## Docker

Use the `POST` endpoint on the Docker container to upload articles to either database; this will upload 10 articles from the Guardian API.

If you're hosting a shared database, run `docker compose up --build`; this loads up the app with uvicorn at `0.0.0.0:8000`.

#### Streamlit (Docker)

Run `docker compose build`(if not built previously) & `docker compose up` in rag/services/streamlit

#### Streamlit (Locally)

Ensure you've pip installed requirements in your local virtual env. 

On Mac, run the script at dev/run.sh 

On Windows, run the script at dev/run.bat (by clicking it in file explorer)


## Local PostgreSQL

Run `uvicorn services.postgres_controller:app --reload --port 8001`.

(You will need to activate your venv & `pip install -r requirements.txt`)


## Local Clickhouse

Run `uvicorn services.clickhouse_controller:app --reload --port 8000`.

(You will need to activate your venv & `pip install -r requirements.txt`)

## Local Cassandra

Run `uvicorn services.cassandra.cassandra_controller:app --reload`.

## Local Grafana

1. `cd` into the `llm` folder.
2. Run `docker-compose up`; this will create a Docker container for Grafana on port `3000`.
3. In your browser, open `localhost:3000`, and login using username `admin` and password `admin`.
4. Add a new data source with the following parameters:
   1. **Server address**: the IP of your container.
   2. **Server port**: `8123`
   3. **Protocol**: `HTTP`
   4. **Skip TLS Verify**: `true`
   5. **Username**: `user`
   6. **Password**: `default`
   7. **Default database**: `guardian`
   8. **Default table**: `langchain_metrics`
5. Save and test the data source, and verify it connects successfully.
6. Import `dashboard.json` from the `llm` folder.
7. You should now have a local Grafana with metrics data; the metrics tab on the Streamlit application should now also work.

# Endpoints

## GET

curl "http://localhost:8000/related-articles?query=<query>"

## POST

curl -X POST "http://localhost:8000/upload-articles"

# License

[MIT](https://choosealicense.com/licenses/mit/)