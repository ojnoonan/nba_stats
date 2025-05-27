#!/bin/bash
# Script to test database connection and basic functionality

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define paths
DATA_DIR="$SCRIPT_DIR/data"
DB_FILE="$DATA_DIR/nba_stats.db"

echo "Testing database connection at $DB_FILE"

# Make sure the database exists
if [ ! -f "$DB_FILE" ]; then
    echo "Database file doesn't exist. Running cleanup to find or create one..."
    ./cleanup_databases.sh

    if [ ! -f "$DB_FILE" ]; then
        echo "Still can't find a database. Creating a new one with the correct schema..."
        ./fix_database_schema.sh
    fi
fi

# Try a simple query to verify connection
echo "Testing basic database query..."
if sqlite3 "$DB_FILE" "SELECT 1;" > /dev/null 2>&1; then
    echo "Basic connection test passed."
else
    echo "ERROR: Failed to connect to the database."
    echo "Check file permissions and make sure the database file is not corrupted."
    exit 1
fi

# Check for the DataUpdateStatus table and cancellation_requested column
echo "Testing table and column existence..."
if sqlite3 "$DB_FILE" "SELECT cancellation_requested FROM data_update_status LIMIT 1;" > /dev/null 2>&1; then
    echo "Schema test passed. The data_update_status table and cancellation_requested column exist."
else
    echo "Schema test failed. Running fix script..."
    ./fix_missing_column.sh

    # Test again
    if sqlite3 "$DB_FILE" "SELECT cancellation_requested FROM data_update_status LIMIT 1;" > /dev/null 2>&1; then
        echo "Schema fixed successfully."
    else
        echo "ERROR: Schema issues persist after fix attempt."
        echo "You may need to recreate the database with ./recreate_database.sh"
        exit 1
    fi
fi

echo "All database tests passed successfully."
echo "The database connection is working and the schema is correct."
