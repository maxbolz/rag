░█████████     ░███      ░██████     ░███████   ░████████              
░██     ░██   ░██░██    ░██   ░██    ░██   ░██  ░██    ░██             
░██     ░██  ░██  ░██  ░██           ░██    ░██ ░██    ░██   ░███████  
░█████████  ░█████████ ░██  █████    ░██    ░██ ░████████   ░██        
░██   ░██   ░██    ░██ ░██     ██    ░██    ░██ ░██     ░██  ░███████  
░██    ░██  ░██    ░██  ░██  ░███    ░██   ░██  ░██     ░██        ░██ 
░██     ░██ ░██    ░██   ░█████░█    ░███████   ░█████████   ░███████  
```

# RAG Database Benchmarking Suite

This repository is designed for **benchmarking popular Retrieval-Augmented Generation (RAG) databases**. It enables you to:

- **Measure latency** for reading and writing data to various vector databases.
- **Visualize metrics** and compare performance using a built-in Streamlit dashboard and Grafana.
- **Easily extend** the framework to support new database providers.
- **Modify and experiment** with the codebase to suit your research or production needs.

---

## Features

- **Streamlit Dashboard**: Query databases, visualize results, and compare metrics interactively.
- **Extensible Structure**: Add new database providers with minimal code changes.
- **Dockerized Services**: Each database runs in its own Docker service for easy setup and isolation.
- **Metrics Visualization**: Out-of-the-box Grafana dashboard for latency and token usage.

---

## Quick Start

### 1. Clone & Install

**Note:** You need to have Docker installed

```bash
git clone <this-repo>
cd rag
```

**Set up LangChain and LangSmith**

To visualize metrics, you will need to set up Langchain/Langsmith tracking. It is free and easy.

1. Create Langchain Account
2. Get API Key
3. Create a project

Keep note of your API Key and Project name, you will need those later.


### 2. Environment Setup

Create a `.env` file in the project root:

```env
# Guardian API related information
GUARDIAN_API_KEY=<your key here>

# Claude related information
ANTHROPIC_API_KEY=<your key here>

# Langsmith related information
LANGSMITH_API_KEY=<your key here>
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_PROJECT=<name of your langsmith project>
LANGSMITH_TRACING="true"
LANGSMITH_API_KEY="<your-key>"

DATABASE_TYPE="<name of database>"
HOST="localhost" or shared IPv4 address 
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

## DEV
If you want to use the LLM and/or use the POST steps of the langchain pipeline, set the variables USE_POST and USE_LLM to "true"
in your .env file.

# Endpoints

## GET

curl "http://localhost:8000/related-articles?query=<query>"

## POST

curl -X POST "http://localhost:8000/upload-articles"

# License

# POSTGRES related information
POSTGRES_DB=<name of your database>
POSTGRES_USER=<name of your user to log in with the client>
POSTGRES_PASSWORD=<password of the user>
POSTGRES_PORT=<port postgres will run on, normally 5432>
```

#### 3. Run Services

You have the option to choose between ClickHouse, PostgreSQL, and Cassandra as databases to use in benchmarking.

You can run any of them by the following (this example sets up ClickHouse):

```bash
cd services/clickhouse
docker compose up --build
```

```bash
cd services/streamlit
docker compose up --build
```

Your streamlit application should now be running. 

### 4. Visualize Metrics with Grafana

- The Streamlit service automatically creates a Grafana dashboard within the app, accessble at `https://localhost:8501`.

---

## Benchmarking & Querying

- Use the Streamlit dashboard to run queries against any configured database.
- Latency and token usage metrics are automatically collected and visualized.
- You can choose from Single Question, Multi Batch Question (simulating concurrent users), and Multi Batch Multi Questions (simulating multiple users with different questions).

---

## Adding a New Database Provider

1. **Create a new folder** under `/services` (e.g., `/services/mydb`).
2. **Add your Docker setup** (`Dockerfile`, `docker-compose.yml`) and controller/DAO code.
3. **Extend the `Database` Enum** in `llm/llm_utils/langchain_pipeline.py`:

   ```python
   class Database(Enum):
       CLICKHOUSE = ("clickhouse", 8000)
       POSTGRES = ("postgres", 8001)
       CASSANDRA = ("cassandra", 8003)
       MYDB = ("mydb", <your-port>)
   ```

4. **Implement your controller** to expose the required endpoints (`/related-articles`, `/upload-articles`).
5. **Update the dashboard** (if needed) to include your new provider in the selection.

---

## Customization & Extensibility

- The codebase is modular—add new database backends by following the existing service structure.
- The Streamlit dashboard auto-detects available databases from the `Database` Enum.
- Metrics collection is built-in; extend or modify as needed for your research.

---

## License

[MIT](https://choosealicense.com/licenses/mit/)


---

**Happy benchmarking!**

--- 