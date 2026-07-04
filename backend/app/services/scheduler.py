import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.services.collector import collect_and_save_data

logger = logging.getLogger(__name__)


async def scheduled_collect(interval_seconds: int = 300):
    """
    Фоновая задача сбора метрик.
    Работает в бесконечном цикле с обработкой ошибок.
    """
    logger.info(f"[SCHEDULER] Запуск сбора метрик каждые {interval_seconds} сек")
    
    while True:
        try:
            async with async_session() as db:
                await collect_and_save_data(db)
                logger.info("[SCHEDULER] Сбор метрик успешно завершён")
        except Exception as e:
            logger.error(f"[SCHEDULER] Ошибка сбора метрик: {e}")
        
        await asyncio.sleep(interval_seconds)
