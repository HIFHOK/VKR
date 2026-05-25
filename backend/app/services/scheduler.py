import asyncio
from app.db.session import async_session
from app.services.collector import collect_and_save_data
from app.services.aggregator import aggregate_metrics

async def scheduled_collect(interval_seconds: int = 300):
    """Периодический сбор метрик каждые N секунд"""
    counter = 0
    while True:
        async with async_session() as db:
            try:
                await collect_and_save_data(db)
                counter += 1
                print(f"[SCHEDULER] Сбор #{counter} завершён, следующий через {interval_seconds}с")
                
                # Каждые 12 циклов (раз в час при interval=300с) запускаем агрегацию
                if counter % 12 == 0:
                    print("[SCHEDULER] Запуск часовой агрегации...")
                    await aggregate_metrics(db, period_hours=1)
            except Exception as e:
                print(f"[SCHEDULER] Ошибка: {e}")
        await asyncio.sleep(interval_seconds)