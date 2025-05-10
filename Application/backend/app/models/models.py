from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class Team(Base):
    __tablename__ = "teams"

    team_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    abbreviation = Column(String, nullable=False, unique=True)
    conference = Column(String)
    division = Column(String)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    logo_url = Column(String)
    loading_progress = Column(Integer, default=0)  # Progress percentage for roster loading
    roster_loaded = Column(Boolean, default=False)  # Flag to indicate if roster is fully loaded
    games_loaded = Column(Boolean, default=False)  # Flag to indicate if games are fully loaded
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationships - specify foreign keys explicitly
    players = relationship("Player", back_populates="team", foreign_keys="Player.current_team_id")
    previous_players = relationship("Player", foreign_keys="Player.previous_team_id")
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")

class Player(Base):
    __tablename__ = "players"

    player_id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    current_team_id = Column(Integer, ForeignKey("teams.team_id"))
    previous_team_id = Column(Integer, ForeignKey("teams.team_id"))
    traded_date = Column(DateTime)
    position = Column(String)
    jersey_number = Column(String)
    is_active = Column(Boolean, default=True)
    headshot_url = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationships - specify foreign keys and overlaps explicitly
    team = relationship("Team", back_populates="players", foreign_keys=[current_team_id])
    previous_team = relationship("Team", foreign_keys=[previous_team_id], overlaps="previous_players")
    game_stats = relationship("PlayerGameStats", back_populates="player")

class Game(Base):
    __tablename__ = "games"

    game_id = Column(String, primary_key=True)  # Changed from Integer to String
    game_date_utc = Column(DateTime, nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    status = Column(String, nullable=False)  # 'Upcoming', 'Live', 'Completed'
    season_year = Column(String, nullable=False)
    playoff_round = Column(String)  # Added field for playoff rounds
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    player_stats = relationship("PlayerGameStats", back_populates="game")

    # Add unique constraints
    __table_args__ = (
        UniqueConstraint('home_team_id', 'away_team_id', 'game_date_utc', 'season_year', name='unique_game_matchup'),
    )

class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"

    stat_id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.player_id"))
    game_id = Column(String, ForeignKey("games.game_id"))  # Changed from Integer to String
    team_id = Column(Integer, ForeignKey("teams.team_id"))
    
    minutes = Column(String)
    points = Column(Integer)
    rebounds = Column(Integer)
    assists = Column(Integer)
    steals = Column(Integer)
    blocks = Column(Integer)
    fgm = Column(Integer)
    fga = Column(Integer)
    fg_pct = Column(Float)
    tpm = Column(Integer)
    tpa = Column(Integer)
    tp_pct = Column(Float)
    ftm = Column(Integer)
    fta = Column(Integer)
    ft_pct = Column(Float)
    turnovers = Column(Integer)
    fouls = Column(Integer)
    plus_minus = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Add unique constraint for composite key
    __table_args__ = (
        UniqueConstraint('player_id', 'game_id', 'team_id', name='unique_player_game_stats'),
    )

    # Relationships
    player = relationship("Player", back_populates="game_stats")
    game = relationship("Game", back_populates="player_stats")
    team = relationship("Team")

class DataUpdateStatus(Base):
    __tablename__ = "data_update_status"

    id = Column(Integer, primary_key=True)  # Remove default=1 to let SQLAlchemy handle it
    last_successful_update = Column(DateTime)
    next_scheduled_update = Column(DateTime)
    is_updating = Column(Boolean, default=False)
    teams_updated = Column(Boolean, default=False)
    players_updated = Column(Boolean, default=False)
    games_updated = Column(Boolean, default=False)
    current_phase = Column(String)  # 'teams', 'players', or 'games'
    last_error = Column(String)
    last_error_time = Column(DateTime)