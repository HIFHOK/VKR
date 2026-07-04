import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models.node import Node
from app.models.resource import Resource
from app.models.hardware import HardwareComponent
from app.models.metric import MetricValue

PROMETHEUS_URL = "http://prometheus:9090"


async def collect_and_save_data(db: AsyncSession):
    """Сбор метрик для всех узлов, ресурсов и компонентов"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        await _collect_resources(db, client)
        
        await _collect_hardware_components(db, client)
    
    await db.commit()


async def _collect_resources(db: AsyncSession, client: httpx.AsyncClient):
    """Сбор метрик для Resource (legacy)"""
    result = await db.execute(select(Resource).join(Node))
    resources = result.scalars().all()
    
    for resource in resources:
        try:
            value = await _query_prometheus(client, resource.metric_query)
            if value is not None:
                record = MetricValue(
                    resource_id=resource.id,
                    hardware_id=None,
                    value=value,
                    timestamp=datetime.utcnow()
                )
                db.add(record)
                resource.current_usage = value
        except Exception as e:
            print(f"Error collecting resource {resource.name}: {e}")


async def _collect_hardware_components(db: AsyncSession, client: httpx.AsyncClient):
    """Сбор метрик для HardwareComponent"""
    result = await db.execute(
        select(HardwareComponent)
        .join(Node)
        .where(HardwareComponent.is_active == True)
    )
    components = result.scalars().all()
    
    for comp in components:
        try:
            value = await _query_prometheus(client, comp.metric_query)
            if value is not None:
                record = MetricValue(
                    resource_id=None,
                    hardware_id=comp.id,
                    value=value,
                    timestamp=datetime.utcnow()
                )
                db.add(record)
                
                comp.current_usage = value
                comp.current_usage_unit = _get_usage_unit(comp.metric_query, comp.max_capacity_unit)
                
        except Exception as e:
            print(f"Error collecting component {comp.name}: {e}")


def _get_usage_unit(metric_query: str, default_unit: str | None) -> str:
    """Определяет единицу измерения для current_usage"""
    if "* 100" in metric_query or "100 -" in metric_query:
        return "%"
    if "rate(" in metric_query and "bytes" in metric_query:
        return "B/s"
    return default_unit or ""


async def _query_prometheus(client: httpx.AsyncClient, query: str) -> float | None:
    """Выполняет PromQL-запрос и возвращает числовое значение"""
    try:
        response = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query}
        )
        data = response.json()
        
        if data.get("status") != "success" or not data["data"]["result"]:
            return None
        
        value = float(data["data"]["result"][0]["value"][1])
        return round(value, 2)
        
    except Exception as e:
        print(f"Prometheus query error: {e}")
        return None
