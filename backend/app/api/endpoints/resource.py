from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.resource import Resource
from app.models.node import Node
from app.schemas.resource import ResourceCreate, ResourceResponse

router = APIRouter()

@router.post("/nodes/{node_id}/resources", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    node_id: int,
    resource_in: ResourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Добавление ресурса (CPU, RAM, Disk) к узлу"""
    
    # Проверяем существование узла
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Создаем ресурс
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

@router.get("/nodes/{node_id}/resources", response_model=list[ResourceResponse])
async def get_node_resources(
    node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение всех ресурсов узла"""
    result = await db.execute(
        select(Resource).where(Resource.node_id == node_id)
    )
    return result.scalars().all()