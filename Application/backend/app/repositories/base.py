"""
Base repository class with common query patterns and optimization utilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import Select

from app.database.database import Base

T = TypeVar("T", bound=Base)


class PaginationResult:
    """Result object for paginated queries."""

    def __init__(
        self,
        items: List[Any],
        total: int,
        page: int,
        per_page: int,
        has_next: bool = False,
        has_prev: bool = False,
    ):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.has_next = has_next
        self.has_prev = has_prev
        self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0


class BaseRepository(Generic[T], ABC):
    """Base repository with common database operations and query optimization."""

    def __init__(self, session: Session, model_class: type[T]):
        self.session = session
        self.model_class = model_class

    def get_by_id(self, entity_id: Union[int, str]) -> Optional[T]:
        """Get entity by primary key."""
        return (
            self.session.query(self.model_class)
            .filter(self.model_class.id == entity_id)
            .first()
        )

    def get_all(self, limit: Optional[int] = None) -> List[T]:
        """Get all entities with optional limit."""
        query = self.session.query(self.model_class)
        if limit:
            query = query.limit(limit)
        return query.all()

    def create(self, **kwargs) -> T:
        """Create a new entity."""
        entity = self.model_class(**kwargs)
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T, **kwargs) -> T:
        """Update an existing entity."""
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        """Delete an entity."""
        self.session.delete(entity)
        self.session.commit()

    def paginate(
        self, query: Query, page: int = 1, per_page: int = 20, max_per_page: int = 100
    ) -> PaginationResult:
        """
        Paginate a query with optimization for large datasets.

        Args:
            query: SQLAlchemy Query object
            page: Page number (1-based)
            per_page: Items per page
            max_per_page: Maximum allowed items per page

        Returns:
            PaginationResult with items and pagination metadata
        """
        # Validate pagination parameters
        page = max(1, page)
        per_page = min(max_per_page, max(1, per_page))

        # Get total count efficiently
        total = query.count()

        # Calculate offset
        offset = (page - 1) * per_page

        # Get items for current page
        items = query.offset(offset).limit(per_page).all()

        # Calculate pagination metadata
        has_prev = page > 1
        has_next = offset + per_page < total

        return PaginationResult(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev,
        )

    def bulk_create(self, entities_data: List[Dict[str, Any]]) -> List[T]:
        """Bulk create entities for improved performance."""
        entities = [self.model_class(**data) for data in entities_data]
        self.session.add_all(entities)
        self.session.commit()
        return entities

    def bulk_update(self, updates: List[Dict[str, Any]]) -> None:
        """Bulk update entities by ID for improved performance."""
        if not updates:
            return

        # Group updates by table for efficiency
        self.session.bulk_update_mappings(self.model_class, updates)
        self.session.commit()

    def exists(self, **filters) -> bool:
        """Check if entity exists with given filters."""
        query = self.session.query(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)
        return query.first() is not None

    def count(self, **filters) -> int:
        """Count entities with optional filters."""
        query = self.session.query(func.count(self.model_class.id))
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)
        return query.scalar()

    def find_by(self, **filters) -> List[T]:
        """Find entities by filters."""
        query = self.session.query(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                if value is None:
                    query = query.filter(getattr(self.model_class, key).is_(None))
                else:
                    query = query.filter(getattr(self.model_class, key) == value)
        return query.all()

    def find_one_by(self, **filters) -> Optional[T]:
        """Find single entity by filters."""
        query = self.session.query(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                if value is None:
                    query = query.filter(getattr(self.model_class, key).is_(None))
                else:
                    query = query.filter(getattr(self.model_class, key) == value)
        return query.first()
