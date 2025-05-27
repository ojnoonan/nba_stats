import asyncio
import logging
import os
import secrets
import sys
import tempfile
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.database import (
    Base,
    clear_session_factory_override,
    set_session_factory_override,
)

# Then import the other dependencies
from app.main import app, get_db

# Import models first as they register with Base.metadata
from app.models.models import DataUpdateStatus, Game, Player, PlayerGameStats, Team

# Use a temp directory for test databases
test_db_dir = tempfile.mkdtemp()
print(f"Test database directory: {test_db_dir}")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


@pytest.fixture(scope="function")
def test_db_file_config() -> tuple[str, str]:
    """Generates a unique database URL and file path for a single test."""
    # Create a unique database file for each test
    db_file = os.path.join(test_db_dir, f"test_{secrets.token_hex(8)}.db")
    db_url = f"sqlite+aiosqlite:///{db_file}"
    return db_url, db_file


# Initialize a new session maker for each test
@pytest.fixture(scope="function")
async def db(
    test_db_file_config: tuple[str, str],
) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database for each test using a unique file."""
    db_url, db_file_path = test_db_file_config

    engine = create_async_engine(
        db_url,
        poolclass=NullPool,  # Disable connection pool
        connect_args={"check_same_thread": False},  # Allow concurrent access
        echo=False,
    )

    try:
        TestingSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create tables
        async with engine.begin() as conn:
            try:
                # First drop all tables to ensure clean state (in case file existed)
                await conn.run_sync(Base.metadata.drop_all)
                # Then create all tables defined in our models
                await conn.run_sync(Base.metadata.create_all)
                # Enable foreign key support for SQLite
                await conn.execute(text("PRAGMA foreign_keys=ON"))
            except Exception as e:
                print(f"Error during table creation: {str(e)}")
                raise

        # Start the test session
        async with TestingSessionLocal() as session:
            try:
                await session.begin()
                try:
                    # Create DataUpdateStatus row
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
                        last_successful_update=None,
                        next_scheduled_update=None,
                        last_error=None,
                        last_error_time=None,
                        teams_last_update=None,
                        players_last_update=None,
                        games_last_update=None,
                        components={},
                    )
                    session.add(status)
                    await session.commit()

                    yield session

                    # Rollback any pending changes from the test
                    await session.rollback()
                except Exception as e:
                    await session.rollback()
                    raise e
            finally:
                await session.close()
    finally:
        await engine.dispose()
        # Delete the test database file
        if os.path.exists(db_file_path):
            try:
                os.remove(db_file_path)
            except OSError as e:
                # Log error if file deletion fails, but don't fail the test run for it
                print(f"Warning: Error deleting test database file {db_file_path}: {e}")


# Test client
@pytest.fixture
def client(
    db: AsyncSession, test_db_file_config: tuple[str, str]
) -> Generator[TestClient, None, None]:
    """Get a TestClient instance using the test database session and config."""

    db_url, _ = test_db_file_config  # Use the same URL as the db fixture

    # Store the original database URL
    original_db_url = os.environ.get("DATABASE_URL")

    # Set test database URL for the application
    os.environ["DATABASE_URL"] = db_url

    # We need to clean the app dependency overrides before each test
    # This ensures no dependencies from previous tests are lingering
    app.dependency_overrides.clear()

    # Define the db dependency override for this test
    async def override_get_db():
        try:
            yield db
        finally:
            # Session 'db' is managed by the 'db' fixture (commit/rollback/close)
            pass

    # Create a session factory that always returns the test session
    def test_session_factory():
        return db

    app.dependency_overrides[get_db] = override_get_db

    # Override the session factory to use the test session
    set_session_factory_override(test_session_factory)

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        clear_session_factory_override()
        # Restore original database URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        elif (
            "DATABASE_URL" in os.environ
        ):  # If it was set by us and not originally present
            del os.environ["DATABASE_URL"]


@pytest.fixture(scope="function")
async def test_team(db):
    """Create a test team"""
    try:
        # Create team
        team = Team(
            team_id=1,
            name="Test Team",
            abbreviation="TST",
            conference="Test Conference",
            division="Test Division",
            wins=50,
            losses=32,
            logo_url="https://example.com/test-team.svg",
            loading_progress=0,
            roster_loaded=False,
            games_loaded=False,
        )
        db.add(team)
        await db.commit()
        await db.refresh(team)

        yield team

    finally:
        # Cleanup
        await db.execute(text("DELETE FROM teams WHERE team_id = 1"))
        await db.commit()


@pytest.fixture(scope="function")
async def test_player(db, test_team):
    """Create a test player"""
    try:
        player = Player(
            player_id=1,
            full_name="Test Player",
            first_name="Test",
            last_name="Player",
            current_team_id=test_team.team_id,
            position="G",
            jersey_number="23",
            is_active=True,
            is_loaded=False,
            headshot_url="https://example.com/test-player.png",
        )
        db.add(player)
        await db.commit()
        await db.refresh(player)

        yield player

    finally:
        # Cleanup
        await db.execute(text("DELETE FROM players WHERE player_id = 1"))
        await db.commit()


@pytest.fixture(scope="function")
async def test_away_team(db):
    """Create a test away team"""
    try:
        team = Team(
            team_id=2,
            name="Away Team",
            abbreviation="AWAY",
            conference="Away Conference",
            division="Away Division",
            wins=45,
            losses=37,
            logo_url="https://example.com/away-team.svg",
            loading_progress=100,
            roster_loaded=True,
            games_loaded=True,
        )
        db.add(team)
        await db.commit()
        await db.refresh(team)

        yield team

    finally:
        # Cleanup
        await db.execute(text("DELETE FROM teams WHERE team_id = 2"))
        await db.commit()


@pytest.fixture(scope="function")
async def test_game(db, test_team, test_away_team):
    """Create a test game"""
    try:
        game = Game(
            game_id="0022300001",
            game_date_utc=datetime(
                2025, 5, 9, tzinfo=timezone.utc
            ),  # Added timezone info
            home_team_id=test_team.team_id,
            away_team_id=test_away_team.team_id,
            home_score=105,
            away_score=98,
            status="Completed",
            season_year="2024-25",
            is_loaded=False,  # Explicitly set to false for tests that check loading
        )
        db.add(game)
        await db.commit()
        await db.refresh(game)

        yield game

    finally:
        # Cleanup
        await db.execute(text("DELETE FROM games WHERE game_id = '0022300001'"))
        await db.commit()


@pytest.fixture(scope="function")
async def test_player_stats(db, test_player, test_game, test_team):
    """Create test player statistics"""
    try:
        stats = PlayerGameStats(
            player_id=test_player.player_id,
            game_id=test_game.game_id,
            team_id=test_team.team_id,
            minutes="32:45",
            points=25,
            rebounds=10,
            assists=8,
            steals=2,
            blocks=1,
            fgm=10,
            fga=20,
            fg_pct=0.500,
            tpm=2,
            tpa=6,
            tp_pct=0.333,
            ftm=3,
            fta=4,
            ft_pct=0.750,
            turnovers=2,
            fouls=3,
            plus_minus=12,
        )
        db.add(stats)
        await db.commit()
        await db.refresh(stats)

        yield stats

    finally:
        # Cleanup
        await db.execute(
            text(
                "DELETE FROM player_game_stats WHERE player_id = 1 AND game_id = '0022300001'"
            )
        )
        await db.commit()
