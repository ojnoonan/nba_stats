import asyncio
import os

from app.database.database import SQLALCHEMY_DATABASE_FILE_TO_USE, Base, engine


async def init_db():
    """Initialize the database by creating all tables"""
    # Print where the database is being created
    print(f"Initializing database at: {SQLALCHEMY_DATABASE_FILE_TO_USE}")

    # Make sure the directory exists
    os.makedirs(os.path.dirname(SQLALCHEMY_DATABASE_FILE_TO_USE), exist_ok=True)

    # Create all tables using async engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print(f"Database successfully initialized at {SQLALCHEMY_DATABASE_FILE_TO_USE}")


if __name__ == "__main__":
    print("Creating database tables...")
    asyncio.run(init_db())
    print("Database tables created successfully.")
