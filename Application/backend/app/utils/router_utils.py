import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_session_factory
from app.models.models import DataUpdateStatus

# Type variable for SQLAlchemy model
ModelType = TypeVar("ModelType")
logger = logging.getLogger(__name__)


class RouterUtils:
    @staticmethod
    async def get_entity_or_404(
        db: AsyncSession, model_class: Type[ModelType], entity_id: Any, id_field: str
    ) -> ModelType:
        try:
            stmt = select(model_class).filter(
                getattr(model_class, id_field) == entity_id
            )
            result = await db.execute(stmt)
            entity = result.scalar_one_or_none()

            if entity is None:
                entity_type = model_class.__name__.lower()
                raise HTTPException(
                    status_code=404, detail=f"{entity_type.capitalize()} not found"
                )

            return entity
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving {model_class.__name__} with {id_field}={entity_id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def check_update_status(db: AsyncSession) -> Optional[DataUpdateStatus]:
        stmt = select(DataUpdateStatus)
        result = await db.execute(stmt)
        status = result.scalar_one_or_none()

        if status and status.is_updating:
            raise HTTPException(
                status_code=400, detail="An update is already in progress"
            )

        return status

    @staticmethod
    def create_background_task(
        background_tasks: BackgroundTasks, task_function: Callable, *args, **kwargs
    ) -> Dict[str, str]:
        background_tasks.add_task(task_function, *args, **kwargs)
        return {"message": "Task initiated"}

    @staticmethod
    async def create_async_session_task(
        task_function: Callable, *args, **kwargs
    ) -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            try:
                await task_function(session, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in background task: {str(e)}")
                await session.rollback()
                raise
