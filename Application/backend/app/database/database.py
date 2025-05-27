import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm.session import Session

from app.core.settings import settings

# Database configuration using centralized settings
SQLALCHEMY_DATABASE_URL = settings.database.url
SQLALCHEMY_DATABASE_FILE_TO_USE = settings.database._get_db_file_path()


# Define the Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.database.echo,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=True,  # expire state on commit to ensure fresh reads
    autocommit=False,
    autoflush=False,
)

# Global variable to allow overriding the session factory during tests
_session_factory_override = None


def get_session_factory():
    """Get the current session factory, allowing for test overrides."""
    return (
        _session_factory_override
        if _session_factory_override is not None
        else AsyncSessionLocal
    )


def set_session_factory_override(factory):
    """Override the session factory (for testing purposes)."""
    global _session_factory_override
    _session_factory_override = factory


def clear_session_factory_override():
    """Clear the session factory override."""
    global _session_factory_override
    _session_factory_override = None


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Initialize database
async def init_db():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
