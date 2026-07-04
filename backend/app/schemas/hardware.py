from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class HardwareComponentBase(BaseModel):
    component_type: str
    component_id: str
    name: str
    max_capacity: Optional[float] = None
    max_capacity_unit: Optional[str] = None
    metric_query: str
    component_metadata: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class HardwareComponentResponse(HardwareComponentBase):
    id: int
    node_id: int
    current_usage: Optional[float] = None
    current_usage_unit: Optional[str] = None
    is_active: bool
    discovered_at: datetime
    updated_at: Optional[datetime] = None
