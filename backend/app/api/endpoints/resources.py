from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.resource import Resource
from app.models.node import Node
from app.schemas.resource import ResourceCreate, ResourceResponse
from app.services.collector import collect_and_save_data

router = APIRouter()

@router.get("/nodes", response_model=list[ResourceResponse])
async def list_nodes(db: AsyncSession = Depends(get_db)):
    """Получить список всех узлов"""
    result = await db.execute(select(Node))
    nodes = result.scalars().all()
    return nodes

@router.get("/nodes/{node_id}/resources", response_model=list[ResourceResponse])
async def list_resources(node_id: int, db: AsyncSession = Depends(get_db)):
    """Получить все ресурсы для конкретного узла"""
    result = await db.execute(
        select(Resource).where(Resource.node_id == node_id)
    )
    resources = result.scalars().all()
    return resources

@router.post("/nodes/{node_id}/resources", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    node_id: int,
    resource_in: ResourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Добавление ресурса (CPU, RAM) к узлу"""
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    new_resource = Resource(
        node_id=node_id,
        name=resource_in.name,
        unit=resource_in.unit,
        metric_query=resource_in.metric_query,
        type="compute"
    )
    
    db.add(new_resource)
    await db.commit()
    await db.refresh(new_resource)
    return new_resource

@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить узел"""
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.delete(node)
    await db.commit()

@router.post("/collect")
async def trigger_collect(db: AsyncSession = Depends(get_db)):
    """Ручной запуск сбора метрик (для тестов)"""
    await collect_and_save_data(db)
    return {"status": "Collection finished"}

@router.delete("/nodes/{node_id}/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(node_id: int, resource_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить ресурс"""
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.node_id == node_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    await db.delete(resource)
    await db.commit()