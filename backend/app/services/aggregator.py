from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from datetime import datetime, timedelta
from app.models.metric import MetricValue
from app.models.hardware import HardwareComponent
from app.models.aggregated import AggregatedData


async def aggregate_metrics(db: AsyncSession, hours: int = 1) -> int:
    """
    Агрегация метрик с фиксированными часовыми окнами.
    Гарантирует отсутствие дублей при повторных вызовах.
    """
    end_time = datetime.utcnow()
    
    # 🔑 Выравниваем границы периода по началу часа (например, 13:00:00, 14:00:00)
    period_end = end_time.replace(minute=0, second=0, microsecond=0)
    period_start = period_end - timedelta(hours=hours)

    result = await db.execute(
        select(HardwareComponent).where(HardwareComponent.is_active == True)
    )
    components = result.scalars().all()

    count = 0
    for comp in components:
        metrics_result = await db.execute(
            select(MetricValue).where(
                and_(
                    MetricValue.hardware_id == comp.id,
                    MetricValue.timestamp >= period_start,
                    MetricValue.timestamp < period_end
                )
            )
        )
        values = [m.value for m in metrics_result.scalars().all() if m.value is not None]

        if len(values) >= 2:
            # Удаляем старую запись за этот же период (если есть)
            await db.execute(
                delete(AggregatedData).where(
                    and_(
                        AggregatedData.hardware_id == comp.id,
                        AggregatedData.period_start == period_start
                    )
                )
            )

            agg = AggregatedData(
                hardware_id=comp.id,
                period_start=period_start,
                period_end=period_end,
                min_value=min(values),
                max_value=max(values),
                avg_value=sum(values) / len(values),
                record_count=len(values)
            )
            db.add(agg)
            count += 1

    await db.commit()
    return count