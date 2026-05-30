from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    address = Column(String(45), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 🔥 ДОБАВЬТЕ ЭТО ПОЛЕ:
    prometheus_instance = Column(String(255), nullable=True)
    
    # Relationships
    resources = relationship("Resource", back_populates="node")
    hardware = relationship("HardwareComponent", back_populates="node", cascade="all, delete-orphan")