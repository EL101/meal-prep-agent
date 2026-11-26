from fastapi import FastAPI

from app.api import health, users

app = FastAPI(title="Meal Prep Agent API")
app.include_router(health.router)
app.include_router(users.router)
