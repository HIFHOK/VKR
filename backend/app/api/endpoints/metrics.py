from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["metrics"])
async def list_metrics():
    """Список метрик (заглушка)"""
    return {"metrics": []}