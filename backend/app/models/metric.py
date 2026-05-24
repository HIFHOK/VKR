from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # prometheus metric name
    unit = Column(String(30), nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    resource = relationship("Resource", back_populates="metrics")
    values = relationship("MetricValue", back_populates="metric", cascade="all, delete-orphan")
    aggregated = relationship("AggregatedData", back_populates="metric", cascade="all, delete-orphan")

class MetricValue(Base):
    __tablename__ = "metric_values"
    __table_args__ = (
        Index("idx_metric_values_metric_time", "metric_id", "timestamp", postgresql_using="btree"),
    )
    
    id = Column(Integer, primary_key=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    metric = relationship("Metric", back_populates="values")

class AggregatedData(Base):
    __tablename__ = "aggregated_data"
    __table_args__ = (
        Index("idx_aggregated_metric_period_time", "metric_id", "period", "start_time"),
    )
    
    id = Column(Integer, primary_key=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False)
    period = Column(String(10), nullable=False)  # "1h", "1d", "7d"
    min_value = Column(Float, nullable=False)
    max_value = Column(Float, nullable=False)
    avg_value = Column(Float, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    metric = relationship("Metric", back_populates="aggregated")