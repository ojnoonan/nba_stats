#!/bin/bash
# Script to verify database schema and check for common issues

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define paths
DATA_DIR="$SCRIPT_DIR/data"
DB_FILE="$DATA_DIR/nba_stats.db"

echo "Verifying database at $DB_FILE"

# Check if database file exists
if [ ! -f "$DB_FILE" ]; then
    echo "ERROR: Database file not found!"
    echo "Run ./cleanup_databases.sh to find or create a database."
    exit 1
fi

# Check for various issues
echo "Checking data_update_status table..."
if ! sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='data_update_status';" | grep -q "data_update_status"; then
    echo "ERROR: data_update_status table doesn't exist!"
    echo "Run ./fix_database_schema.sh to create the missing table."
    exit 1
fi

echo "Checking for cancellation_requested column..."
if ! sqlite3 "$DB_FILE" "PRAGMA table_info(data_update_status);" | grep -q "cancellation_requested"; then
    echo "ERROR: cancellation_requested column missing!"
    echo "Run ./fix_missing_column.sh to add the missing column."
    exit 1
fi

echo "Checking teams table..."
if ! sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='teams';" | grep -q "teams"; then
    echo "WARNING: teams table doesn't exist. Basic schema may be incomplete."
    echo "Run ./fix_database_schema.sh to fix this issue."
fi

echo "Checking players table..."
if ! sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='players';" | grep -q "players"; then
    echo "WARNING: players table doesn't exist. Basic schema may be incomplete."
    echo "Run ./fix_database_schema.sh to fix this issue."
fi

echo "Checking games table..."
if ! sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='games';" | grep -q "games"; then
    echo "WARNING: games table doesn't exist. Basic schema may be incomplete."
    echo "Run ./fix_database_schema.sh to fix this issue."
fi

# Verify alembic version table
echo "Checking alembic_version table..."
if ! sqlite3 "$DB_FILE" "SELECT version_num FROM alembic_version;" > /dev/null 2>&1; then
    echo "WARNING: alembic_version table doesn't exist or is corrupted."
    echo "Run ./fix_database_schema.sh to fix this issue."
else
    CURRENT_VERSION=$(sqlite3 "$DB_FILE" "SELECT version_num FROM alembic_version;")
    echo "Current migration version: $CURRENT_VERSION"

    # Check if we're at the latest version
    if [ "$CURRENT_VERSION" != "57f5b3644f4a" ]; then
        echo "WARNING: Database is not at the latest migration version."
        echo "Latest version should be 57f5b3644f4a (add_cancellation_requested_to_dataupdatestatus)"
        echo "Run ./fix_database_schema.sh to apply all migrations."
    else
        echo "Database is at the latest migration version."
    fi
fi

echo "Database verification complete."
echo "No critical issues found in the schema."
echo ""
echo "If you're still experiencing issues, try:"
echo "1. ./fix_missing_column.sh (for cancellation_requested column issues)"
echo "2. ./fix_database_schema.sh (for general schema issues)"
echo "3. ./recreate_database.sh (as a last resort)"
