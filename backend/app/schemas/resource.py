from pydantic import BaseModel, Field
from typing import Optional

class ResourceCreate(BaseModel):
    name: str = Field("cpu_total", min_length=1)  # ← Кавычки!
    unit: str = Field("%", min_length=1)  # ← Кавычки!
    metric_query: str = Field("node_cpu_seconds_total", min_length=1) # Prometheus query: "node_cpu_seconds_total"

class ResourceResponse(BaseModel):
    id: int
    name: str
    unit: str
    metric_query: str
    node_id: int

    class Config:
        from_attributes = True