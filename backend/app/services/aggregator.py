from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.metric import MetricValue, AggregatedData
from app.models.resource import Resource


async def aggregate_metrics(db: AsyncSession, period_hours: int = 1):
    """
    Агрегирует метрики за указанный период.
    Считает MIN, MAX, AVG, COUNT для каждого ресурса.
    """
    since = datetime.utcnow() - timedelta(hours=period_hours)
    
    # Выполняем агрегирующий запрос
    result = await db.execute(
        select(
            MetricValue.resource_id,
            func.min(MetricValue.value).label("min_value"),
            func.max(MetricValue.value).label("max_value"),
            func.avg(MetricValue.value).label("avg_value"),
            func.count(MetricValue.id).label("count")
        )
        .where(MetricValue.timestamp >= since)
        .group_by(MetricValue.resource_id)
    )
    
    # Получаем все строки результата
    rows = result.all()
    aggregated_count = 0
    
    for row in rows:
        # Пропускаем пустые агрегации
        if row.count == 0:
            continue
            
        agg = AggregatedData(
            resource_id=row.resource_id,
            period_start=since,
            period_end=datetime.utcnow(),
            min_value=float(row.min_value) if row.min_value is not None else None,
            max_value=float(row.max_value) if row.max_value is not None else None,
            avg_value=float(row.avg_value) if row.avg_value is not None else None,
            sample_count=row.count
        )
        db.add(agg)
        aggregated_count += 1
    
    try:
        await db.commit()
        print(f"[AGGREGATOR] Агрегировано ресурсов: {aggregated_count}")
    except Exception as e:
        print(f"[AGGREGATOR ERROR] Ошибка при сохранении: {e}")
        await db.rollback()
        raise