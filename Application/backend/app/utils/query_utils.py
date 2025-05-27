"""
Utilities for query building and pagination.
This module provides functions for building standardized database queries
with pagination, filtering, and sorting.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar, Union

from fastapi import Query
from sqlalchemy import and_, or_, select
from sqlalchemy.sql import Select

ModelType = TypeVar("ModelType")
logger = logging.getLogger(__name__)


def paginate_query(stmt: Select, skip: int = 0, limit: int = 100) -> Select:
    """
    Apply pagination to a SQLAlchemy select statement.

    Args:
        stmt: SQLAlchemy select statement
        skip: Number of items to skip
        limit: Maximum number of items to return

    Returns:
        Statement with pagination applied
    """
    return stmt.offset(skip).limit(limit)


def apply_filters(
    stmt: Select, model_class: Type[ModelType], filters: Dict[str, Any]
) -> Select:
    """
    Apply filters to a SQLAlchemy select statement.

    Args:
        stmt: SQLAlchemy select statement
        model_class: The SQLAlchemy model class
        filters: Dictionary of field names and values to filter by

    Returns:
        Statement with filters applied
    """
    for field, value in filters.items():
        if value is not None and hasattr(model_class, field):
            stmt = stmt.filter(getattr(model_class, field) == value)
    return stmt


def apply_date_filter(
    stmt: Select, model_class: Type[ModelType], date_field: str, date_str: Optional[str]
) -> Tuple[Select, bool]:
    """
    Apply date filtering to a SQLAlchemy select statement.

    Args:
        stmt: SQLAlchemy select statement
        model_class: The SQLAlchemy model class
        date_field: The field to filter by date
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Tuple of (statement with date filter applied, success flag)
    """
    if not date_str:
        return stmt, True

    try:
        from datetime import datetime

        import sqlalchemy as sa

        # Parse the date string to a datetime object
        filter_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Filter by date
        if hasattr(model_class, date_field):
            stmt = stmt.filter(
                sa.func.date(getattr(model_class, date_field)) == filter_date.date()
            )
        return stmt, True
    except ValueError:
        return stmt, False
