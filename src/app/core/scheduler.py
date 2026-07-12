import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session
from app.stock.models import RestockConfig
from app.stock.service import run_daily_restock_check

logger = logging.getLogger(__name__)


async def get_active_branches(db: AsyncSession) -> list[str]:
    # Obtener todas las sucursales que tienen auto_restock_activo = 1
    query = select(RestockConfig.branch_id).where(
        RestockConfig.auto_restock_activo == 1)
    result = await db.execute(query)
    return [row[0] for row in result.all()]


async def run_scheduler():
    logger.info("Starting background scheduler for daily restock...")

    # Simple loop to check every day
    while True:
        now = datetime.now(timezone.utc)

        # Ejecutar todos los días a las 11:00 AM UTC (ejemplo), 5:00 AM mexico
        target_hour = 11
        next_run = now.replace(hour=target_hour, minute=0,
                               second=0, microsecond=0)

        if now >= next_run:
            import datetime as dt
            next_run += dt.timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()
        logger.info(
            f"Next daily restock check scheduled in {wait_seconds} seconds.")

        try:
            await asyncio.sleep(wait_seconds)

            # Ejecutar el check
            async with async_session() as session:
                branches = await get_active_branches(session)
                for branch_id in branches:
                    logger.info(
                        f"Running automatic restock for branch {branch_id}")
                    try:
                        await run_daily_restock_check(session, branch_id)
                    except Exception as e:
                        logger.error(
                            f"Error running auto restock for branch {branch_id}: {e}")

        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in scheduler loop: {e}")
            await asyncio.sleep(60)  # Wait a bit before retrying on error
