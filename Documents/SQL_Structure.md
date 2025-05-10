Proposed SQLite Database SchemaThis schema is based on the requirements outlined in the PRD (nba_stats_prd_user_stories_v1).-- Stores information about each NBA team
CREATE TABLE Teams (
    team_id INTEGER PRIMARY KEY, -- Official NBA Team ID
    name TEXT NOT NULL,
    abbreviation TEXT UNIQUE NOT NULL,
    conference TEXT,
    division TEXT,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    logo_url TEXT, -- URL or path to the team logo
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Stores information about each player for the current season
CREATE TABLE Players (
    player_id INTEGER PRIMARY KEY, -- Official NBA Player ID
    full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    current_team_id INTEGER, -- FK to Teams.team_id (can be NULL if free agent?)
    position TEXT,
    jersey_number TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    headshot_url TEXT, -- URL or path to the player headshot
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_team_id) REFERENCES Teams(team_id)
);

-- Stores information about each game in the schedule
CREATE TABLE Games (
    game_id INTEGER PRIMARY KEY, -- Official NBA Game ID
    game_date_utc DATETIME NOT NULL, -- Store game start time in UTC
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status TEXT NOT NULL, -- e.g., 'Upcoming', 'Live', 'Completed'
    season_year TEXT NOT NULL, -- e.g., '2024' or '2024-25'
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES Teams(team_id)
);

-- Stores individual player statistics for a specific game (Box Score)
CREATE TABLE PlayerGameStats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL, -- Team the player played for *in this game*
    minutes TEXT, -- Often stored as 'MM:SS' string
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    fgm INTEGER, -- Field Goals Made
    fga INTEGER, -- Field Goals Attempted
    fg_pct REAL, -- Field Goal Percentage
    tpm INTEGER, -- Three Pointers Made
    tpa INTEGER, -- Three Pointers Attempted
    tp_pct REAL, -- Three Point Percentage
    ftm INTEGER, -- Free Throws Made
    fta INTEGER, -- Free Throws Attempted
    ft_pct REAL, -- Free Throw Percentage
    turnovers INTEGER,
    fouls INTEGER,
    plus_minus INTEGER,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (game_id) REFERENCES Games(game_id),
    FOREIGN KEY (team_id) REFERENCES Teams(team_id),
    UNIQUE (player_id, game_id) -- Ensure only one stat line per player per game
);

-- Optional: Could store calculated seasonal averages to avoid recalculating often
-- CREATE TABLE PlayerSeasonAverages (
--     player_id INTEGER PRIMARY KEY,
--     season_year TEXT NOT NULL,
--     games_played INTEGER,
--     avg_minutes REAL,
--     avg_points REAL,
--     avg_rebounds REAL,
--     avg_assists REAL,
--     -- ... other average stats ...
--     last_calculated DATETIME DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (player_id) REFERENCES Players(player_id)
-- );

-- Optional: Could store calculated Team SoS values
-- CREATE TABLE TeamStrengthOfSchedule (
--     team_id INTEGER PRIMARY KEY,
--     season_year TEXT NOT NULL,
--     sos_played REAL,
--     sos_remaining REAL,
--     last_calculated DATETIME DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (team_id) REFERENCES Teams(team_id)
-- );

-- Stores info about data fetch status
CREATE TABLE DataUpdateStatus (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Ensure only one row
    last_successful_update DATETIME,
    next_scheduled_update DATETIME
);

Notes:player_id, team_id, game_id should ideally correspond to the IDs used by the nba_api.Storing percentages (fg_pct, etc.) might be redundant if FGM/FGA are stored, but can be convenient.Consider adding indices to foreign keys and frequently queried columns (e.g., game_date_utc, player names) for performance.The PlayerSeasonAverages and TeamStrengthOfSchedule tables are optional optimizations. You could calculate these values on-the-fly when requested by the API if preferred, especially for a personal project.The DataUpdateStatus table provides a single place to store the timestamps needed for the navigation bar.