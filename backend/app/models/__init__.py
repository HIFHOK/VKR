from app.models.node import Node
from app.models.resource import Resource
from app.models.metric import Metric, MetricValue, AggregatedData

# Это нужно, чтобы SQLAlchemy увидел все связи при старте
__all__ = ["Node", "Resource", "Metric", "MetricValue", "AggregatedData"]