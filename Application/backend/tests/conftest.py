import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.database.database import Base, get_db
from app.models.models import Team, Player, Game, PlayerGameStats, DataUpdateStatus

# Create test database in memory
SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
TestingSession = scoped_session(TestingSessionLocal)

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    
    try:
        yield session
    finally:
        session.close()
        TestingSession.remove()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create a test client with a clean database for each test"""
    def override_get_db():
        try:
            yield db
        finally:
            db.rollback()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_team(db):
    """Create a test team"""
    team = Team(
        team_id=1,
        name="Test Team",
        abbreviation="TST",
        conference="Test Conference",
        division="Test Division",
        wins=50,
        losses=32,
        logo_url="https://example.com/test-team.svg"
    )
    db.add(team)
    db.commit()
    db.refresh(team)  # Refresh to ensure we have the latest state
    return team

@pytest.fixture
def test_player(db, test_team):
    """Create a test player"""
    player = Player(
        player_id=1,
        full_name="Test Player",
        first_name="Test",
        last_name="Player",
        current_team_id=test_team.team_id,
        position="G",
        jersey_number="23",
        is_active=True,
        headshot_url="https://example.com/test-player.png"
    )
    db.add(player)
    db.commit()
    db.refresh(player)  # Refresh to ensure we have the latest state
    return player

@pytest.fixture
def test_game(db, test_team):
    """Create a test game"""
    game = Game(
        game_id="0022300001",
        game_date_utc=datetime(2025, 5, 9),
        home_team_id=test_team.team_id,
        away_team_id=2,
        home_score=105,
        away_score=98,
        status="Completed",
        season_year="2024-25"
    )
    db.add(game)
    db.commit()
    db.refresh(game)  # Refresh to ensure we have the latest state
    return game

@pytest.fixture
def test_player_stats(db, test_player, test_game, test_team):
    """Create test player statistics"""
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
        plus_minus=12
    )
    db.add(stats)
    db.commit()
    db.refresh(stats)  # Refresh to ensure we have the latest state
    return stats