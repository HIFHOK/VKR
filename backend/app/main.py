from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Импорты роутеров (если файла resources нет, закоментируйте эту строку)
from app.api.endpoints import health, nodes, metrics, resources

app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(nodes.router, prefix=settings.API_V1_PREFIX, tags=["nodes"])
app.include_router(resources.router, prefix=settings.API_V1_PREFIX, tags=["resources"])
app.include_router(metrics.router, prefix=settings.API_V1_PREFIX, tags=["metrics"])

@app.on_event("startup")
async def startup_db():
    # Импортируем модели ВНУТРИ стартапа, чтобы избежать циклических импортов
    from app.models import Node, Resource, Metric, MetricValue, AggregatedData
    from app.db.base import Base
    from app.db.session import engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown_db():
    from app.db.session import engine
    await engine.dispose()

@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} v{settings.APP_VERSION}"}