from fastapi import FastAPI

from app.api import health

app = FastAPI(title="Meal Prep Agent API")
app.include_router(health.router)
