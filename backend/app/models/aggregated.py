from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class AggregatedData(Base):
    """Агрегированные метрики за период"""
    __tablename__ = "aggregated_data"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    
    # Resource — оставлено для совместимости со старыми данными, но без обратной связи
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Основная связь — с компонентами железа
    hardware_id = Column(Integer, ForeignKey("hardware_components.id", ondelete="CASCADE"), nullable=True, index=True)
    
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    min_value = Column(Float, nullable=False)
    max_value = Column(Float, nullable=False)
    avg_value = Column(Float, nullable=False)
    record_count = Column(Integer, nullable=False)

    # Обратная связь только с HardwareComponent (Resource — без back_populates)
    hardware = relationship("HardwareComponent", back_populates="aggregated_metrics")