#!/bin/bash
# This script specifically fixes missing timestamp columns in the data_update_status table

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

# Function to safely add a column if it doesn't exist
add_column_if_missing() {
    local column=$1

    echo "Checking for $column column..."
    if ! sqlite3 "$DB_FILE" "SELECT $column FROM data_update_status LIMIT 1;" > /dev/null 2>&1; then
        echo "Adding missing column: $column"
        sqlite3 "$DB_FILE" "ALTER TABLE data_update_status ADD COLUMN $column DATETIME;"
        if [ $? -eq 0 ]; then
            echo "Successfully added $column column"
        else
            echo "Failed to add $column column"
            return 1
        fi
    else
        echo "$column column already exists"
    fi
    return 0
}

echo "Adding missing timestamp columns..."

# Add each timestamp column
add_column_if_missing "teams_last_update" && \
add_column_if_missing "players_last_update" && \
add_column_if_missing "games_last_update"

# Verify all columns exist
echo "Verifying all timestamp columns..."
if sqlite3 "$DB_FILE" \
    "SELECT teams_last_update, players_last_update, games_last_update FROM data_update_status LIMIT 1;" > /dev/null 2>&1; then
    echo "All timestamp columns are present and correct!"
else
    echo "ERROR: Some timestamp columns are still missing."
    echo "Try running ./fix_database_schema.sh for a complete fix."
    exit 1
fi

echo "Done! The database schema has been updated."
echo
echo "If you're running Docker, restart the containers:"
echo "cd ../../ && docker-compose restart backend"
