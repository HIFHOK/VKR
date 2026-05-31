import os
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.node import Node
from app.models.resource import Resource
from app.services.hardware_discovery import discover_hardware
from pydantic import BaseModel, Field

router = APIRouter()

PROMETHEUS_TARGETS_DIR = "/etc/prometheus/targets"

class NodeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., pattern=r"^(\d{1,3}\.){3}\d{1,3}$|^[0-9a-fA-F:]+$")
    type: str = Field(..., pattern="^(physical|vm|container)$")

class NodeResponse(BaseModel):
    id: int
    name: str
    address: str
    type: str
    status: str

    class Config:
        from_attributes = True

def _create_prometheus_target_file(node_id: int, address: str, instance_name: str):
    target_data = [
        {
            "targets": [f"{address}:9100"],
            "labels": {
                "instance": instance_name,
                "environment": "development",
                "node_id": str(node_id)
            }
        }
    ]
    filename = f"node_{node_id}.json"
    filepath = os.path.join(PROMETHEUS_TARGETS_DIR, filename)
    try:
        with open(filepath, 'w') as f:
            json.dump(target_data, f, indent=2)
    except Exception as e:
        print(f"❌ ERROR: Could not create Prometheus target file: {e}")

def _delete_prometheus_target_file(node_id: int):
    filename = f"node_{node_id}.json"
    filepath = os.path.join(PROMETHEUS_TARGETS_DIR, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"⚠️ Warning: Could not delete Prometheus target file: {e}")

def _create_default_resources(node_id: int, instance_name: str):
    return [
        Resource(
            node_id=node_id, type="cpu", name="CPU Usage", unit="%",
            metric_query=f'100 - (avg(rate(node_cpu_seconds_total{{instance="{instance_name}",mode="idle"}}[1m])) * 100)'
        ),
        Resource(
            node_id=node_id, type="memory", name="RAM Usage", unit="%",
            metric_query=f'(1 - (node_memory_MemAvailable_bytes{{instance="{instance_name}"}} / node_memory_MemTotal_bytes{{instance="{instance_name}"}})) * 100'
        ),
        Resource(
            node_id=node_id, type="disk", name="Disk Usage", unit="%",
            metric_query=f'(1 - (node_filesystem_avail_bytes{{instance="{instance_name}",mountpoint="/" }} / node_filesystem_size_bytes{{instance="{instance_name}",mountpoint="/" }})) * 100'
        ),
        Resource(
            node_id=node_id, type="network", name="Network Usage", unit="B/s",
            metric_query=f'rate(node_network_receive_bytes_total{{instance="{instance_name}",device!="lo"}}[1m])'
        )
    ]

@router.post("/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(node_in: NodeCreate, db: AsyncSession = Depends(get_db)):
    """Создание узла + автоматическая настройка мониторинга"""
    
    # 1. Проверка уникальности имени
    result = await db.execute(select(Node).where(Node.name == node_in.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Node with this name already exists")
    
    # 2. Создаём узел в БД
    db_node = Node(**node_in.model_dump())
    
    # 🔥 АВТОМАТИЧЕСКИ устанавливаем prometheus_instance = имя узла
    db_node.prometheus_instance = node_in.name
    
    db.add(db_node)
    await db.flush()
    
    # 3. Формируем instance-метку
    instance_name = node_in.name
    
    # 4. Создаём файл для Prometheus File SD
    _create_prometheus_target_file(db_node.id, node_in.address, instance_name)
    
    # 5. Создаём стандартные ресурсы для Dashboard
    for resource in _create_default_resources(db_node.id, instance_name):
        db.add(resource)
    
    # 6. Сохраняем всё в БД
    await db.commit()
    await db.refresh(db_node)
    
    # 7. Запускаем авто-обнаружение железа (асинхронно)
    try:
        import asyncio
        asyncio.create_task(discover_hardware(db, db_node.id))
    except Exception as e:
        print(f"⚠️ Warning: Could not trigger hardware discovery: {e}")
    
    return db_node

@router.get("/nodes", response_model=list[NodeResponse])
async def list_nodes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Node).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    _delete_prometheus_target_file(node_id)
    
    await db.delete(node)
    await db.commit()