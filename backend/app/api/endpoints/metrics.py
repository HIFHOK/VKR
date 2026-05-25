from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.metric import MetricValue
from app.models.resource import Resource

router = APIRouter()

@router.get("/{resource_id}/history")
async def get_metric_history(resource_id: int, db: AsyncSession = Depends(get_db)):
    """Получение истории метрик для конкретного ресурса"""
    
    # Проверяем, существует ли ресурс
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Получаем последние 100 записей
    result = await db.execute(
        select(MetricValue)
        .where(MetricValue.resource_id == resource_id)
        .order_by(MetricValue.timestamp.desc())
        .limit(100)
    )
    return result.scalars().all()