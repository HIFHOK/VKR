from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.node import Node
from pydantic import BaseModel, Field

router = APIRouter()

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
        from_attributes = True  # Pydantic v2: включает ORM-режим

@router.post("/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(node_in: NodeCreate, db: AsyncSession = Depends(get_db)):
    """Создание нового узла"""
    result = await db.execute(select(Node).where(Node.name == node_in.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Node with this name already exists")
    
    db_node = Node(**node_in.model_dump())
    db.add(db_node)
    await db.commit()
    await db.refresh(db_node)
    return db_node

@router.get("/nodes", response_model=list[NodeResponse])
async def list_nodes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Список узлов с пагинацией"""
    result = await db.execute(select(Node).offset(skip).limit(limit))
    return result.scalars().all()