from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.metric import MetricValue
#from app.models.aggregated import AggregatedData
from app.services.aggregator import aggregate_metrics

router = APIRouter()

@router.get("/")
async def list_metrics():
    """Список метрик (заглушка)"""
    return {"metrics": []}

@router.get("/{resource_id}/history")
async def get_metric_history(resource_id: int, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Получение истории метрик для ресурса"""
    result = await db.execute(
        select(MetricValue)
        .where(MetricValue.resource_id == resource_id)
        .order_by(MetricValue.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/{resource_id}/stats")
async def get_metric_stats(resource_id: int, db: AsyncSession = Depends(get_db)):
    """Статистика по метрике: MIN, MAX, AVG"""
    result = await db.execute(
        select(
            func.min(MetricValue.value).label("min"),
            func.max(MetricValue.value).label("max"),
            func.avg(MetricValue.value).label("avg"),
            func.count(MetricValue.id).label("count")
        ).where(MetricValue.resource_id == resource_id)
    )
    stats = result.first()
    return {
        "resource_id": resource_id,
        "min": stats.min,
        "max": stats.max,
        "avg": round(stats.avg, 2) if stats.avg else None,
        "records": stats.count
    }

@router.post("/aggregate")
async def trigger_aggregation(period_hours: int = 1, db: AsyncSession = Depends(get_db)):
    """Ручной запуск агрегации метрик"""
    await aggregate_metrics(db, period_hours=period_hours)
    return {"status": "Aggregation finished", "period_hours": period_hours}

#@router.get("/{resource_id}/aggregated")
#async def get_aggregated_data(hardware_id: int, db: AsyncSession = Depends(get_db)):
#    """Получение агрегированных данных"""
#    result = await db.execute(
#        select(AggregatedData)
#        .where(AggregatedData.hardware_id == hardware_id)
#        .order_by(AggregatedData.period_end.desc())
#        .limit(50)
#    )
#    return result.scalars().all()