#!/bin/bash
# This script completely recreates the database from scratch
# Use this if you're experiencing persistent database schema issues

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define paths
DATA_DIR="$SCRIPT_DIR/data"
DB_FILE="$DATA_DIR/nba_stats.db"

echo "WARNING: This will delete your existing database and create a new one."
echo "All your data will be lost."
read -p "Are you sure you want to continue? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Operation cancelled."
    exit 0
fi

echo "Backing up current database (if it exists)..."
if [ -f "$DB_FILE" ]; then
    BACKUP_FILE="$DB_FILE.backup.$(date +%Y%m%d%H%M%S)"
    cp "$DB_FILE" "$BACKUP_FILE"
    echo "Backup created at $BACKUP_FILE"
fi

echo "Deleting the database file..."
rm -f "$DB_FILE"

# Ensure data directory exists with proper permissions
echo "Ensuring data directory exists with proper permissions..."
mkdir -p "$DATA_DIR"
chmod -R 777 "$DATA_DIR"

echo "Running migrations to create schema..."
python3 -m alembic upgrade head

# Verify the database was created correctly
if [ -f "$DB_FILE" ]; then
    echo "New database created successfully at $DB_FILE"

    # Verify schema by checking for the cancellation_requested column
    echo "Verifying database schema..."
    if sqlite3 "$DB_FILE" "SELECT sql FROM sqlite_master WHERE name='data_update_status';" | grep -q "cancellation_requested"; then
        echo "Database schema verification passed! The cancellation_requested column exists."
    else
        echo "WARNING: The database schema appears to be missing expected columns."
        echo "This may indicate an issue with Alembic migrations."

        # Try a direct SQL fix
        echo "Attempting a direct SQL fix..."
        sqlite3 "$DB_FILE" "ALTER TABLE data_update_status ADD COLUMN cancellation_requested BOOLEAN NOT NULL DEFAULT 0;" 2>/dev/null

        echo "Schema fixed manually."
    fi
else
    echo "ERROR: Failed to create new database!"
    exit 1
fi

echo "Database has been recreated with a clean schema."
echo "You will need to reload your data."
echo
echo "If you're using Docker, restart your containers with:"
echo "cd ../../ && docker-compose restart backend"
