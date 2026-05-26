from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base  # ← Обязательно!


class HardwareComponent(Base):
    __tablename__ = "hardware_components"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    component_type = Column(String(20), nullable=False, index=True)
    component_id = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    
    max_capacity = Column(Float)
    max_capacity_unit = Column(String(20))
    
    current_usage = Column(Float)
    current_usage_unit = Column(String(20))
    
    metric_query = Column(String(500), nullable=False)
    
    # ← Исправлено: metadata → component_metadata (reserved word in SQLAlchemy)
    component_metadata = Column("metadata", JSON, default=dict)
    
    is_active = Column(Boolean, default=True)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связь с узлом
    node = relationship("Node", back_populates="hardware")
    metrics = relationship("MetricValue", back_populates="hardware", cascade="all, delete-orphan")
    aggregated_metrics = relationship("AggregatedData", back_populates="hardware", cascade="all, delete-orphan")