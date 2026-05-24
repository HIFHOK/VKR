import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.config import settings

class PrometheusCollector:
    """Сервис для сбора метрик из Prometheus"""
    
    def __init__(self):
        self.base_url = settings.PROMETHEUS_URL
        self.timeout = settings.PROMETHEUS_TIMEOUT
    
    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "15s"
    ) -> Optional[Dict[str, Any]]:
        """Выполняет range query к Prometheus API"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {
                "query": query,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "step": step
            }
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/query_range",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "success":
                    return data.get("data")
                return None
                
            except httpx.HTTPError as e:
                # Логирование ошибки (добавьте logger позже)
                print(f"Prometheus query error: {e}")
                return None
    
    async def get_metric_value(
        self,
        metric_name: str,
        instance: Optional[str] = None
    ) -> Optional[float]:
        """Получает последнее значение метрики"""
        query = metric_name
        if instance:
            query += f'{{instance="{instance}"}}'
        
        result = await self.query_range(
            query=query,
            start=datetime.utcnow(),
            end=datetime.utcnow(),
            step="1m"
        )
        
        if result and result.get("result"):
            values = result["result"][0].get("values", [])
            if values:
                return float(values[-1][1])
        return None