#!/bin/bash
# This script sets up the development environment to use the correct database location

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define paths
DATA_DIR="$SCRIPT_DIR/Application/backend/data"
DB_FILE="$DATA_DIR/nba_stats.db"

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"
chmod -R 777 "$DATA_DIR"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo "No database found at $DB_FILE. Running cleanup to find or create one..."
    ./Application/backend/cleanup_databases.sh
fi

# Verify and fix database schema if needed
if [ -f "$DB_FILE" ]; then
    echo "Verifying database schema..."
    if ! sqlite3 "$DB_FILE" "SELECT cancellation_requested FROM data_update_status LIMIT 1;" > /dev/null 2>&1; then
        echo "Schema issue detected with cancellation_requested column. Attempting to fix..."
        ./Application/backend/fix_missing_column.sh
    else
        echo "Database schema looks correct!"
    fi
fi

# Set the environment variable for development
export NBA_STATS_DATA_DIR="$DATA_DIR"

echo "Development environment configured to use database at: $DB_FILE"

# Run migrations to ensure schema is up to date
echo "Running database migrations..."
cd Application/backend
python3 -m alembic upgrade head

# Verify migrations worked
echo "Verifying migrations..."
if ! sqlite3 "$DB_FILE" "SELECT cancellation_requested FROM data_update_status LIMIT 1;" > /dev/null 2>&1; then
    echo "WARNING: Migration didn't fix the schema. Attempting direct SQL fix..."
    sqlite3 "$DB_FILE" "ALTER TABLE data_update_status ADD COLUMN cancellation_requested BOOLEAN NOT NULL DEFAULT 0;" 2>/dev/null

    # Verify again
    if ! sqlite3 "$DB_FILE" "SELECT cancellation_requested FROM data_update_status LIMIT 1;" > /dev/null 2>&1; then
        echo "ERROR: Could not fix the database schema. You may need to recreate the database."
        echo "Run ./Application/backend/recreate_database.sh if this issue persists."
        exit 1
    else
        echo "Direct SQL fix successful!"
    fi
else
    echo "Database schema successfully updated!"
fi
cd ../..

# Run the regular dev script with the environment variable set
./dev.sh
