from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.endpoints import health, nodes, metrics, resources  # ← Все импорты
from app.services.scheduler import scheduled_collect

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(health.router, prefix=settings.API_V1_PREFIX, tags=["health"])
app.include_router(nodes.router, prefix=settings.API_V1_PREFIX, tags=["nodes"])
app.include_router(resources.router, prefix=settings.API_V1_PREFIX, tags=["resources"])
app.include_router(metrics.router, prefix=settings.API_V1_PREFIX + "/metrics", tags=["metrics"])  # ← ВАЖНО: prefix с /metrics!

@app.on_event("startup")
async def startup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(scheduled_collect(interval_seconds=300))