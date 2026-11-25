"""Run with:  uv run arq app.worker.settings.WorkerSettings"""

from typing import Any

import httpx
from arq.connections import RedisSettings
from arq.cron import cron

from app.config import get_settings
from app.worker.tasks import carry_over_inventory, generate_plan, scan_inventory


async def startup(ctx: dict[str, Any]) -> None:
    ctx["http"] = httpx.AsyncClient(timeout=20)


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["http"].aclose()


class WorkerSettings:
    functions = [generate_plan, scan_inventory]
    cron_jobs = [cron(carry_over_inventory, weekday="sun", hour=3, minute=0)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    job_timeout = 600  # Claude + optimizer can take a few minutes
    max_jobs = 10
