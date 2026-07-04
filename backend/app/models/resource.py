from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(30), nullable=False)
    name = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=False)
    metric_query = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    node = relationship("Node", back_populates="resources")
    metrics = relationship("MetricValue", back_populates="resource", cascade="all, delete-orphan")
