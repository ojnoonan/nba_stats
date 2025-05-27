import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DataUpdateStatus

logger = logging.getLogger(__name__)


async def get_or_create_status(db: AsyncSession) -> DataUpdateStatus:
    """Get the existing DataUpdateStatus or create a new one if none exists."""
    # First check for the status with ID=1 which should always be pre-seeded
    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()

    if status:
        return status

    # If no status with ID=1 exists, check for any status records
    stmt = select(DataUpdateStatus)
    result = await db.execute(stmt)
    all_statuses = result.scalars().all()

    if len(all_statuses) > 0:
        # If any exist, use the first one
        status = all_statuses[0]
        # Make sure it has ID=1
        status.id = 1
        await db.commit()
        return status

    logger.critical(
        "CRITICAL: DataUpdateStatus with id=1 not found. This record should be pre-seeded."
    )
    # Create new status if none exists - ONLY as a failsafe to prevent application crashes
    new_status = DataUpdateStatus(
        id=1,  # Always use ID=1
        is_updating=False,
        current_phase=None,
        cancellation_requested=False,
        teams_updated=False,
        players_updated=False,
        games_updated=False,
        teams_percent_complete=0,
        players_percent_complete=0,
        games_percent_complete=0,
        components={},  # Initialize empty components dictionary
    )
    try:
        db.add(new_status)
        await db.commit()
        await db.refresh(new_status)
        logger.warning("Created failsafe DataUpdateStatus with id=1")
        return new_status
    except Exception as e:
        # If we got here, something is seriously wrong - likely a unique constraint violation
        logger.critical(f"Failed to create DataUpdateStatus: {e}")
        await db.rollback()
        # Try one more time to get existing status
        stmt = select(DataUpdateStatus).filter_by(id=1)
        result = await db.execute(stmt)
        status = result.scalar_one_or_none()
        if status:
            return status
        raise  # If we still can't find it, let the exception propagate


async def initialize_update_status(
    db: AsyncSession, component: str
) -> DataUpdateStatus:
    """Initialize the status for a component update"""
    status = await get_or_create_status(db)

    # Reset status flags
    status.is_updating = True
    status.current_phase = component
    status.cancellation_requested = False
    status.last_error = None
    status.last_error_time = None

    # Initialize per-component flags
    is_updated = False
    setattr(status, f"{component}_updated", is_updated)
    setattr(status, f"{component}_percent_complete", 0)

    # Initialize components dict if needed
    if not isinstance(status.components, dict):
        status.components = {}

    # Initialize component status and ensure it matches model fields
    if component not in status.components:
        status.components[component] = {}
    status.components[component].update(
        {
            "updated": is_updated,  # Match the model field
            "percent_complete": 0,
            "last_error": None,
            "last_update": None,
        }
    )

    status.current_detail = f"Starting {component} update"
    await db.commit()
    return status


async def set_update_error(db: AsyncSession, component: str, error: str) -> None:
    """Set error state for a component update"""
    status = await get_or_create_status(db)

    # Reset flags
    status.is_updating = False
    status.current_phase = None
    status.last_error = error
    status.last_error_time = now = datetime.now(timezone.utc)

    # Set component-specific flags
    setattr(status, f"{component}_updated", False)

    # Update component status
    components = status.components if isinstance(status.components, dict) else {}
    components[component] = components.get(component, {})
    components[component].update(
        {
            "updated": False,
            "last_error": error,
            "percent_complete": 0,
            "last_update": None,
        }
    )
    status.components = components

    await db.commit()


async def finalize_update(db: AsyncSession, component: str) -> None:
    """Mark a component update as completed successfully"""
    status = await get_or_create_status(db)

    now = datetime.now(timezone.utc)
    # Reset general flags
    status.is_updating = False
    status.current_phase = None
    status.last_error = None
    status.last_error_time = None

    # Set component-specific flags
    setattr(status, f"{component}_updated", True)
    setattr(status, f"{component}_last_update", now)
    setattr(status, f"{component}_percent_complete", 100)
    status.current_detail = f"{component.capitalize()} update complete"

    # Update component status
    components = status.components if isinstance(status.components, dict) else {}
    components[component] = components.get(component, {})
    components[component].update(
        {
            "updated": True,
            "last_update": now,
            "percent_complete": 100,
            "last_error": None,
        }
    )
    status.components = components

    await db.commit()
