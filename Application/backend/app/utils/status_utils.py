"""Status utility functions for managing update status."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.models import DataUpdateStatus

logger = logging.getLogger(__name__)


async def get_or_create_status(db: AsyncSession) -> DataUpdateStatus:
    """Get or create the singleton DataUpdateStatus record."""
    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()

    if not status:
        status = DataUpdateStatus(
            id=1,
            is_updating=False,
            cancellation_requested=False,
            teams_updated=False,
            players_updated=False,
            games_updated=False,
            teams_percent_complete=0,
            players_percent_complete=0,
            games_percent_complete=0,
            current_phase=None,
            current_detail=None,
            components={},
        )
        db.add(status)
        await db.commit()
        await db.refresh(status)

    return status


async def initialize_status(component: str, db: AsyncSession) -> None:
    """Initialize component status at the start of an update."""
    status = await get_or_create_status(db)

    # Initialize nested status
    if not isinstance(status.components, dict):
        status.components = {}
    if component not in status.components:
        status.components[component] = {}

    status.components[component].update(
        {
            "updated": False,
            "percent_complete": 0,
            "last_error": None,
            "start_time": datetime.now(timezone.utc).isoformat(),
        }
    )
    # Mark the JSON field as modified so SQLAlchemy detects the change
    flag_modified(status, "components")

    # Initialize flat fields
    status.is_updating = True
    status.current_phase = component
    status.cancellation_requested = False
    status.last_error = None
    setattr(status, f"{component}_updated", False)
    setattr(status, f"{component}_percent_complete", 0)
    setattr(status, f"{component}_last_update", None)

    await db.commit()


async def update_progress(
    component: str, processed: int, total: int, db: AsyncSession
) -> None:
    """Update progress for a component during an update."""
    status = await get_or_create_status(db)

    percent_complete = int((processed / total) * 100) if total > 0 else 0

    # Update nested status
    if isinstance(status.components, dict) and component in status.components:
        status.components[component].update(
            {"percent_complete": percent_complete, "updated": percent_complete == 100}
        )
        # Mark the JSON field as modified so SQLAlchemy detects the change
        flag_modified(status, "components")

    # Update flat fields
    setattr(status, f"{component}_percent_complete", percent_complete)
    setattr(status, f"{component}_updated", percent_complete == 100)
    if percent_complete == 100:
        setattr(status, f"{component}_last_update", datetime.now(timezone.utc))

    await db.commit()


async def finalize_component(component: str, db: AsyncSession) -> None:
    """Finalize status for a component after successful completion."""
    status = await get_or_create_status(db)
    now = datetime.now(timezone.utc)

    # Update nested status
    if isinstance(status.components, dict) and component in status.components:
        status.components[component].update(
            {
                "updated": True,
                "percent_complete": 100,
                "last_error": None,
                "last_update": now.isoformat(),
            }
        )
        # Mark the JSON field as modified so SQLAlchemy detects the change
        flag_modified(status, "components")

    # Update flat fields
    setattr(status, f"{component}_updated", True)
    setattr(status, f"{component}_percent_complete", 100)
    setattr(status, f"{component}_last_update", now)

    # Check if we should stop updating
    # Stop if: all components are done OR if this is the only active component
    remaining_components = [c for c in ["teams", "players", "games"] if c != component]
    all_components_done = all(
        getattr(status, f"{c}_updated", False) for c in remaining_components
    )
    is_single_component_update = status.current_phase == component

    if all_components_done or is_single_component_update:
        status.is_updating = False
        status.current_phase = None
        status.last_successful_update = now
        status.next_scheduled_update = None  # Let the scheduler set this

    await db.commit()


async def handle_component_error(
    component: str, error_msg: str, db: AsyncSession
) -> None:
    """Handle error for a component during update."""
    status = await get_or_create_status(db)
    now = datetime.now(timezone.utc)

    # Update nested status
    if isinstance(status.components, dict) and component in status.components:
        status.components[component].update({"last_error": error_msg, "updated": False})
        # Mark the JSON field as modified so SQLAlchemy detects the change
        flag_modified(status, "components")

    # Update flat fields
    setattr(status, f"{component}_updated", False)
    status.current_phase = None
    status.is_updating = False
    status.last_error = error_msg
    status.last_error_time = now

    await db.commit()

    await db.commit()
