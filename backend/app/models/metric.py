from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class MetricValue(Base):
    """Сырые значения метрик"""
    __tablename__ = "metric_values"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=True, index=True)
    hardware_id = Column(Integer, ForeignKey("hardware_components.id", ondelete="CASCADE"), nullable=True, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    resource = relationship("Resource", back_populates="metrics")
    hardware = relationship("HardwareComponent", back_populates="metrics")