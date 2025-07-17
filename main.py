from fastapi import FastAPI
from postgres_routes.postgres_routes import router as psql_router

app = FastAPI()

app.include_router(psql_router, prefix="/psql")  # Attach the router with prefix