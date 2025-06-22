from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager, asynccontextmanager
import os

# Import settings after the core module is available
try:
    from app.core.config import settings
    # Use settings for database configuration
    DATA_DIR = settings.nba_stats_data_dir
    SQLALCHEMY_DATABASE_URL = settings.database_url
except ImportError:
    # Fallback for when settings aren't available (e.g., during initial setup)
    DATA_DIR = os.getenv('NBA_STATS_DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
    SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{DATA_DIR}/nba_stats.db")

# Ensure data directory exists
os.makedirs(os.path.dirname(SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')), exist_ok=True)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for synchronous database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def get_async_db():
    """Async context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()