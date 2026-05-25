from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Metric(Base):
    """Метаданные метрики (справочник)"""
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    unit = Column(String(50))

    values = relationship("MetricValue", back_populates="metric", cascade="all, delete-orphan")


class MetricValue(Base):
    """Конкретные значения метрик во времени"""
    __tablename__ = "metric_values"

    id = Column(Integer, primary_key=True, index=True)
    # ← ЭТО КРИТИЧЕСКИ ВАЖНО: ForeignKey на resources.id
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # ← Связь с Resource (back_populates должен совпадать)
    resource = relationship("Resource", back_populates="metrics")
    
    # Опциональная связь со справочником метрик
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="SET NULL"), nullable=True)
    metric = relationship("Metric", back_populates="values")


class AggregatedData(Base):
    """Агрегированные данные (MIN, MAX, AVG за период)"""
    __tablename__ = "aggregated_data"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    min_value = Column(Float)
    max_value = Column(Float)
    avg_value = Column(Float)
    sample_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resource = relationship("Resource")