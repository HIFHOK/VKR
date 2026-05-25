from pydantic import BaseModel, Field

class ResourceCreate(BaseModel):
    name: str = Field("cpu_total", min_length=1)
    unit: str = Field("%", min_length=1)
    metric_query: str = Field("node_cpu_seconds_total", min_length=1)

class ResourceResponse(BaseModel):
    id: int
    name: str
    unit: str
    metric_query: str
    node_id: int

    class Config:
        from_attributes = True