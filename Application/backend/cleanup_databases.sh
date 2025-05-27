#!/bin/bash
# This script cleans up duplicate database files to avoid confusion
# It ensures we're only using the database in the Docker volume

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting database cleanup..."

# List of database files to check and their locations
ROOT_DB="$SCRIPT_DIR/../../nba_stats.db"
BACKEND_DB="$SCRIPT_DIR/nba_stats.db"
BACKEND_NBA_DB="$SCRIPT_DIR/nba.db"
DATA_DB="$SCRIPT_DIR/data/nba_stats.db"

# Create the data directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/data"

# Check if any DB exists to migrate data from
if [ -f "$DATA_DB" ]; then
    echo "Found database in data directory, will use this as the primary database."
    PRIMARY_DB="$DATA_DB"
elif [ -f "$BACKEND_DB" ]; then
    echo "Found database in backend directory, will move this to the data directory."
    PRIMARY_DB="$BACKEND_DB"
elif [ -f "$ROOT_DB" ]; then
    echo "Found database in root directory, will move this to the data directory."
    PRIMARY_DB="$ROOT_DB"
elif [ -f "$BACKEND_NBA_DB" ]; then
    echo "Found nba.db in backend directory, will move this to the data directory and rename."
    PRIMARY_DB="$BACKEND_NBA_DB"
else
    echo "No existing database found. Will create a new empty one in the data directory."
    touch "$DATA_DB"
    PRIMARY_DB="$DATA_DB"
fi

# If the primary DB isn't already in the data directory, copy it there
if [ "$PRIMARY_DB" != "$DATA_DB" ]; then
    echo "Copying $PRIMARY_DB to $DATA_DB"
    cp "$PRIMARY_DB" "$DATA_DB"
    echo "Database has been copied to the data directory."
fi

# Now create backups of all other DBs before removing them
if [ "$PRIMARY_DB" != "$ROOT_DB" ] && [ -f "$ROOT_DB" ]; then
    echo "Backing up root database."
    cp "$ROOT_DB" "${ROOT_DB}.bak"
    echo "Removing root database."
    rm -f "$ROOT_DB"
fi

if [ "$PRIMARY_DB" != "$BACKEND_DB" ] && [ -f "$BACKEND_DB" ]; then
    echo "Backing up backend database."
    cp "$BACKEND_DB" "${BACKEND_DB}.bak"
    echo "Removing backend database."
    rm -f "$BACKEND_DB"
fi

if [ "$PRIMARY_DB" != "$BACKEND_NBA_DB" ] && [ -f "$BACKEND_NBA_DB" ]; then
    echo "Backing up backend nba database."
    cp "$BACKEND_NBA_DB" "${BACKEND_NBA_DB}.bak"
    echo "Removing backend nba database."
    rm -f "$BACKEND_NBA_DB"
fi

echo "Database cleanup complete."
echo "All data is now stored in $DATA_DB"
echo "This path will be mounted as a Docker volume when using docker-compose."
echo "Note: This ensures your data survives container restarts."
