```
`7MM"""Mq.        db       .g8"""bgd  
  MM   `MM.      ;MM:    .dP'     `M  
  MM   ,M9      ,V^MM.   dM'       `  
  MMmmdM9      ,M  `MM   MM           
  MM  YM.      AbmmmqMA  MM.    `7MMF'
  MM   `Mb.   A'     VML `Mb.     MM  
.JMML. .JMM..AMA.   .AMMA. `"bmmmdPY  
```

Getting Set Up
---
1. Get an API Key from Guardian delivered to your email by requesting one from https://bonobo.capi.gutools.co.uk/register/developer.

2. Create a .env file at the project root (`/rag/`) that contains `GUARDIAN_API_KEY="<<your-guardian-api-key>>"`

3. Install psql & remember the login credentials you create (probably username "postgres", and password something easy like "pass" or "root") 

    Create a PSQL Database on localhost post 5432 named "guardian" by running a psql shell with `psql -U postgres -h localhost -p 5432` 

    In the PSQL command shell, run `CREATE DATABASE guardian;`. You should see it spit back out `CREATE DATABASE`. 

    From the PSQL command shell, connect to the new db with `\c guardian`

4. Add your psql db credentials to your .env
      ```
      # PSQL CREDENTIALS
      POSTGRES_DB="guardian"
      POSTGRES_USER="postgres"
      POSTGRES_PASSWORD="<<your-password>>"
      POSTGRES_HOST="localhost"
      POSTGRES_PORT=5432
      
      GUARDIAN_API_KEY=""
      ```
5. Run docker for Postgres database
    cd rag 
    docker-compose -f docker/docker-compose.yml up -d


Setting Up Virtual Environment
--
Create a Virtual Environment (If you haven't already): `python -m venv .venv`

Activate Venv for MacOS: `source .venv/bin/activate`

Activate Venv for Windows: `.venv/Scripts/activate`

`pip install requirements.txt`

Running
--
Mac: In working directory, run `chmod +x run.sh && ./run.sh`

Windows: Open `run.bat`

Pulling New Documents
--

To reach clickhouse endpoints:
python -m clickhouse_services.scripts.[name of script]


To reach postgres endpoints:
--

If you're running the server and database entirely on your own, run:
1. `uvicorn postgres_services.postgres_controller:app --reload`

If you're hosting the shared database, run:
1. `cd docker`
2. `docker compose up --build` (This loads up the app with uvicorn at 0.0.0.0 port 8000)

To POST articles to PG Database:
`curl -X POST http://localhost:8000/upload-articles` will upload 10 unique Guardian articles 
- If the DB is hosted from someone else, replace <<localhost>> with their IP address

To GET articles from the PG Database:
- `curl http://localhost:8000/related-articles?query=<< your query as a URL-encoded string >>`
- EX: `curl http://localhost:8000/related-articles?query=whats%20trump%20doing`
- If the DB is hosted from someone else, replace <<localhost>> with their IP address
