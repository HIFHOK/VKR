import httpx
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.metric import MetricValue
from app.models.resource import Resource

PROMETHEUS_URL = "http://prometheus:9090"

async def collect_and_save_data(db: AsyncSession):
    """
    Сбор метрик из Prometheus и сохранение в БД
    """
    # Получаем все ресурсы
    result = await db.execute(select(Resource))
    resources = result.scalars().all()
    
    if not resources:
        print("Нет ресурсов для сбора данных")
        return
    
    async with httpx.AsyncClient() as client:
        for resource in resources:
            try:
                # Запрос к Prometheus
                query_url = f"{PROMETHEUS_URL}/api/v1/query?query={resource.metric_query}"
                response = await client.get(query_url)
                data = response.json()
                
                if data.get("status") == "success" and data["data"]["result"]:
                    # Получаем значение
                    value = float(data["data"]["result"][0]["value"][1])
                    
                    print(f"[OK] {resource.name}: {value} {resource.unit}")
                    
                    # Сохраняем в БД
                    record = MetricValue(
                        resource_id=resource.id,
                        value=value,
                        timestamp=datetime.utcnow()
                    )
                    db.add(record)
                else:
                    print(f"[WARN] Нет данных для {resource.name}")
                    
            except Exception as e:
                print(f"[ERROR] Ошибка сбора {resource.name}: {e}")
    
    await db.commit()