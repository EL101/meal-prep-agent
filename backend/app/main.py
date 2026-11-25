from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, inventory, plans, profile, ratings
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.queue = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    yield
    await app.state.queue.aclose()


def create_app(*, use_lifespan: bool = True) -> FastAPI:
    app = FastAPI(title="Meal Prep Agent API", lifespan=lifespan if use_lifespan else None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for module in (health, profile, inventory, plans, ratings):
        app.include_router(module.router)
    return app


app = create_app()
