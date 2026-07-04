import io
import csv
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.hardware import HardwareComponent
from app.models.aggregated import AggregatedData
from app.models.node import Node
from app.services.aggregator import aggregate_metrics

router = APIRouter()


@router.post("/aggregate")
async def trigger_aggregation(
    period: int = Query(1, ge=1, le=168, description="Период в часах (1-168)"),
    db: AsyncSession = Depends(get_db)
):
    """Запустить агрегацию всех компонентов за указанный период"""
    count = await aggregate_metrics(db, period)
    return {
        "status": "done",
        "aggregated_count": count,
        "period_hours": period
    }


@router.get("/hardware/{component_id}/aggregated")
async def get_aggregated_metrics(
    component_id: int,
    period: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Получить агрегированные метрики компонента"""
    result = await db.execute(
        select(HardwareComponent).where(
            HardwareComponent.id == component_id,
            HardwareComponent.is_active == True
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Component not found")
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=period)
    
    result = await db.execute(
        select(AggregatedData).where(
            and_(
                AggregatedData.hardware_id == component_id,
                AggregatedData.period_start >= start_time
            )
        ).order_by(AggregatedData.period_start.desc()).limit(50)
    )
    
    return [
        {
            "period_start": r.period_start.isoformat(),
            "period_end": r.period_end.isoformat(),
            "min": r.min_value,
            "max": r.max_value,
            "avg": round(r.avg_value, 2),
            "count": r.record_count
        }
        for r in result.scalars().all()
    ]


@router.get("/nodes/{node_id}/aggregated/export")
async def export_aggregated_data(
    node_id: int,
    period: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Экспорт агрегированных данных узла в CSV (Excel-compatible)"""
    node_res = await db.execute(select(Node).where(Node.id == node_id))
    node = node_res.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=period)
    
    result = await db.execute(
        select(HardwareComponent, AggregatedData)
        .join(AggregatedData, HardwareComponent.id == AggregatedData.hardware_id)
        .where(
            HardwareComponent.node_id == node_id,
            HardwareComponent.is_active == True,
            AggregatedData.period_start >= start_time
        )
        .order_by(HardwareComponent.component_type, HardwareComponent.name, AggregatedData.period_start)
    )
    
    rows = result.all()
    if not rows:
        raise HTTPException(status_code=404, detail="No aggregated data found for this period")
    
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    writer.writerow([
        "Node Name",
        "Component ID", 
        "Component Name", 
        "Type",
        "Period Start", 
        "Period End",
        "Min Value", 
        "Max Value", 
        "Avg Value", 
        "Record Count"
    ])
    
    for hw, agg in rows:
        writer.writerow([
            node.name,
            hw.component_id,
            hw.name,
            hw.component_type,
            agg.period_start.strftime("%Y-%m-%d %H:%M:%S"),
            agg.period_end.strftime("%Y-%m-%d %H:%M:%S"),
            str(round(agg.min_value, 2)).replace('.', ','),
            str(round(agg.max_value, 2)).replace('.', ','),
            str(round(agg.avg_value, 2)).replace('.', ','),
            agg.record_count
        ])
    
    csv_content = stream.getvalue()
    
    csv_data_with_bom = '\ufeff' + csv_content
    
    filename = f"aggregated_{node.name}_period_{period}h.csv"
    
    return Response(
        content=csv_data_with_bom,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
