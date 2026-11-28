from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, users
from app.config import get_settings


def add_cors(app: FastAPI, origins: list[str]) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )


app = FastAPI(title="Meal Prep Agent API")
add_cors(app, get_settings().cors_origins)
app.include_router(health.router)
app.include_router(users.router)
