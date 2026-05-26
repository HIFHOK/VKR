from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.db.session import get_db
from app.models.hardware import HardwareComponent
from app.models.node import Node
from app.models.metric import MetricValue
from app.services.hardware_discovery import discover_hardware
from app.schemas.hardware import HardwareComponentResponse

router = APIRouter()


@router.post("/nodes/{node_id}/hardware/discover", response_model=list[HardwareComponentResponse])
async def trigger_hardware_discovery(
    node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Запустить автообнаружение аппаратных компонентов для узла.
    Сканирует Prometheus и создаёт записи для CPU, RAM, Disk, Network.
    """
    # Проверка существования узла
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Запуск обнаружения
    await discover_hardware(db, node_id)
    
    # Возврат списка компонентов
    result = await db.execute(
        select(HardwareComponent).where(
            HardwareComponent.node_id == node_id,
            HardwareComponent.is_active == True
        ).order_by(HardwareComponent.component_type, HardwareComponent.component_id)
    )
    return result.scalars().all()


@router.get("/nodes/{node_id}/hardware", response_model=list[HardwareComponentResponse])
async def list_hardware(
    node_id: int,
    component_type: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список аппаратных компонентов узла.
    
    - **component_type**: фильтр по типу (cpu, ram, disk, network)
    """
    query = select(HardwareComponent).where(
        HardwareComponent.node_id == node_id,
        HardwareComponent.is_active == True
    )
    
    if component_type:
        query = query.where(HardwareComponent.component_type == component_type)
    
    result = await db.execute(
        query.order_by(HardwareComponent.component_type, HardwareComponent.component_id)
    )
    return result.scalars().all()


@router.get("/hardware/{component_id}/metrics")
async def get_component_metrics(
    component_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить историю метрик для конкретного компонента.
    
    - **limit**: количество последних записей (по умолчанию 100)
    """
    result = await db.execute(
        select(MetricValue).where(
            MetricValue.hardware_id == component_id
        ).order_by(MetricValue.timestamp.desc()).limit(limit)
    )
    metrics = result.scalars().all()
    
    # Возвращаем в прямом порядке (от старых к новым)
    return [
        {
            "id": m.id,
            "value": m.value,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None
        }
        for m in reversed(metrics)
    ]


@router.get("/nodes/{node_id}/hardware/summary")
async def get_hardware_summary(node_id: int, db: AsyncSession = Depends(get_db)):
    """
    Сводная информация по всем компонентам узла с текущей нагрузкой.
    """
    result = await db.execute(
        select(HardwareComponent).where(
            HardwareComponent.node_id == node_id,
            HardwareComponent.is_active == True
        )
    )
    components = result.scalars().all()
    
    summary = {
        "node_id": node_id,
        "updated_at": datetime.utcnow().isoformat(),
        "components": []
    }
    
    for comp in components:
        # Вычисляем процент использования
        usage_percent = None
        if comp.current_usage is not None:
            if comp.metric_query and ("* 100" in comp.metric_query or "100 -" in comp.metric_query):
                # Метрика уже в процентах
                usage_percent = min(comp.current_usage, 100)
            elif comp.max_capacity and comp.max_capacity > 0:
                # Считаем процент от максимума
                usage_percent = min((comp.current_usage / comp.max_capacity) * 100, 100)
        
        # Определяем статус
        if usage_percent is None:
            status_level = "unknown"
        elif usage_percent >= 90:
            status_level = "critical"
        elif usage_percent >= 70:
            status_level = "warning"
        else:
            status_level = "ok"
        
        summary["components"].append({
            "id": comp.id,
            "type": comp.component_type,
            "component_id": comp.component_id,
            "name": comp.name,
            "capacity": {
                "value": comp.max_capacity,
                "unit": comp.max_capacity_unit
            } if comp.max_capacity else None,
            "current_usage": {
                "value": comp.current_usage,
                "unit": comp.current_usage_unit,
                "percent": round(usage_percent, 1) if usage_percent is not None else None
            },
            "status": status_level,
            "discovered_at": comp.discovered_at.isoformat() if comp.discovered_at else None
        })
    
    return summary


@router.get("/hardware/{component_id}", response_model=HardwareComponentResponse)
async def get_hardware_component(
    component_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить информацию о конкретном компоненте по ID.
    """
    result = await db.execute(
        select(HardwareComponent).where(
            HardwareComponent.id == component_id,
            HardwareComponent.is_active == True
        )
    )
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    return component