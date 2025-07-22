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
# PSQL CREDENTIALS
POSTGRES_DB="guardian"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="<your-password>"
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432

GUARDIAN_API_KEY="<your-key>"
```

3. Install PostgreSQL; ensure you **write down your login somewhere safe**.

4. Create a PostgreSQL database on `localhost:5432` named `guardian` by running `psql -U postgres -h localhost -p 5432`.

5. In pgAdmin, run `CREATE DATABASE guardian;`.

6. Connect to the database with `\c guardian` in your Powershell.

7. Run Docker for PostgreSQL using `docker-compose -f docker/docker-compose.yml up -d`

8. Install the project requirements using `pip install requirements.txt`; if you do not have a virtual environment set up, do that first!

# Running

## Mac

In working directory, run 
```chmod +x run.sh && ./run.sh```.

## Windows

Run `run.bat`.

## Docker

Use the `POST` endpoint on the Docker container to upload articles to either database; this will upload 10 articles from the Guardian API.

If you're hosting a shared database, run `docker compose up --build`; this loads up the app with uvicorn at `0.0.0.0:8000`.

## Local PostgreSQL

Run `uvicorn services.postgres_controller:app --reload`.

## Local Clickhouse

Run `uvicorn services.clickhouse_controller:app --reload`.

# Endpoints

## GET

`http://localhost:8000/related-articles?query=<query>`

## POST

`http://localhost:8000/upload-articles`

# License

[MIT](https://choosealicense.com/licenses/mit/)