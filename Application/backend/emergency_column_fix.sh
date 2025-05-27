#!/bin/bash
# This script is a direct SQL fix for the "no column named cancellation_requested" error
# It can be run inside the Docker container during development

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the database location
DATABASE_PATH="/app/data/nba_stats.db"
if [ ! -f "$DATABASE_PATH" ]; then
  # Try local path for development
  DATABASE_PATH="$SCRIPT_DIR/data/nba_stats.db"
fi

echo "Attempting to fix database at $DATABASE_PATH..."

# Check if the database file exists
if [ ! -f "$DATABASE_PATH" ]; then
  echo "ERROR: Database file not found at $DATABASE_PATH"
  exit 1
fi

# Apply the direct SQL fix
echo "Adding cancellation_requested column to data_update_status table..."
sqlite3 "$DATABASE_PATH" "ALTER TABLE data_update_status ADD COLUMN cancellation_requested BOOLEAN NOT NULL DEFAULT 0;"

# Verify the fix worked
if sqlite3 "$DATABASE_PATH" "SELECT cancellation_requested FROM data_update_status LIMIT 1;" > /dev/null 2>&1; then
  echo "SUCCESS: Column added successfully!"
  echo "You may need to restart the application for changes to take effect."
else
  echo "ERROR: Failed to add column. The table may not exist or there might be another issue."
  echo "Consider running fix_database_schema.sh instead."
fi
