#!/bin/bash
# This script directly fixes the "no column named cancellation_requested" error
# by adding the missing column to the database

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define paths
DATA_DIR="$SCRIPT_DIR/data"
DB_FILE="$DATA_DIR/nba_stats.db"

# Ensure players table has is_loaded column
echo "Adding is_loaded column to players table if missing..."
sqlite3 "$DB_FILE" "ALTER TABLE players ADD COLUMN is_loaded BOOLEAN DEFAULT 0 NOT NULL;" || true

echo "Checking for database at $DB_FILE"
if [ ! -f "$DB_FILE" ]; then
    echo "Database file not found! Running cleanup script first..."
    ./cleanup_databases.sh
fi

echo "Adding missing column to data_update_status table..."

# First try running the migration
echo "Attempting to run migrations first..."
python3 -m alembic upgrade head

# Directly add the column if still needed
echo "Attempting direct SQL fix..."
sqlite3 "$DB_FILE" "SELECT cancellation_requested FROM data_update_status LIMIT 1;" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Adding column directly via SQL..."
    sqlite3 "$DB_FILE" "ALTER TABLE data_update_status ADD COLUMN cancellation_requested BOOLEAN NOT NULL DEFAULT 0;"

    # Verify the fix worked
    sqlite3 "$DB_FILE" "SELECT cancellation_requested FROM data_update_status LIMIT 1;" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Fix successful! The column has been added."
    else
        echo "Fix failed. You may need to recreate the database."
        echo "Run ./recreate_database.sh if this issue persists."
    fi
else
    echo "Column already exists! No fix needed."
fi

echo "Done."
echo
echo "If you're running Docker, restart the containers:"
echo "cd ../../ && docker-compose restart backend"
