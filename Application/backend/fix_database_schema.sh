#!/bin/bash
# This script fixes database schema issues by running Alembic migrations

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define paths
DATA_DIR="$SCRIPT_DIR/data"
DB_FILE="$DATA_DIR/nba_stats.db"

echo "Checking for database at $DB_FILE"
if [ ! -f "$DB_FILE" ]; then
    echo "Database file not found! Running cleanup script first..."
    ./cleanup_databases.sh
fi

echo "Running database migrations..."
python3 -m alembic upgrade head

# Function to check and add a column if missing
check_and_add_column() {
    local table=$1
    local column=$2
    local type=$3
    local default=$4

    if ! sqlite3 "$DB_FILE" "SELECT $column FROM $table LIMIT 1;" > /dev/null 2>&1; then
        echo "Adding missing column: $column"
        if [ -n "$default" ]; then
            sqlite3 "$DB_FILE" "ALTER TABLE $table ADD COLUMN $column $type DEFAULT $default;"
        else
            sqlite3 "$DB_FILE" "ALTER TABLE $table ADD COLUMN $column $type;"
        fi
    fi
}

# Verify schema by checking each required column
echo "Verifying database schema..."
if [ -f "$DB_FILE" ]; then
    # Check for required table
    if ! sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='data_update_status';" | grep -q "data_update_status"; then
        echo "ERROR: data_update_status table doesn't exist!"
        echo "Running full migrations again..."
        python3 -m alembic upgrade head
    fi

    # Check and add each required column
    check_and_add_column "data_update_status" "cancellation_requested" "BOOLEAN" "0"
    check_and_add_column "data_update_status" "teams_last_update" "DATETIME" "NULL"
    check_and_add_column "data_update_status" "players_last_update" "DATETIME" "NULL"
    check_and_add_column "data_update_status" "games_last_update" "DATETIME" "NULL"
    check_and_add_column "data_update_status" "teams_percent_complete" "INTEGER" "0"
    check_and_add_column "data_update_status" "players_percent_complete" "INTEGER" "0"
    check_and_add_column "data_update_status" "games_percent_complete" "INTEGER" "0"
    check_and_add_column "data_update_status" "current_detail" "TEXT" "NULL"

    echo "Verifying fixes..."
    if sqlite3 "$DB_FILE" "SELECT teams_last_update, players_last_update, games_last_update FROM data_update_status LIMIT 1;" > /dev/null 2>&1; then
        echo "Database schema verification successful!"
    else
        echo "WARNING: Schema issues persist. You may need to recreate the database."
        echo "Run ./recreate_database.sh if this issue persists."
    fi
else
    echo "ERROR: Database file not found at $DB_FILE after migrations!"
    echo "Please check your database configuration."
fi

echo "Database schema has been updated!"
echo "If you're running Docker, you may need to restart the containers:"
echo "cd ../../ && docker-compose restart backend"
