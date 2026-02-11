"""Celery task for checking and marking critical rides.

Runs every 5 minutes via Celery Beat.
Calls the existing check_critical_rides() async function from ride_service.
"""

import asyncio
import logging

from app.celery_app import celery_app
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.critical_rides.check_critical_rides_task")
def check_critical_rides_task():
    """Periodic task: mark unassigned rides < 3h as CRITICAL."""
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_run_check())
        return result
    finally:
        loop.close()


async def _run_check() -> dict:
    """Run the critical rides check within an async DB session."""
    from app.services.ride_service import check_critical_rides

    async with AsyncSessionLocal() as session:
        try:
            critical_rides = await check_critical_rides(session)
            await session.commit()
            count = len(critical_rides)
            if count > 0:
                logger.warning(f"Marked {count} ride(s) as CRITICAL")
            else:
                logger.info("No critical rides found")
            return {"critical_count": count}
        except Exception:
            await session.rollback()
            logger.exception("Error checking critical rides")
            raise
