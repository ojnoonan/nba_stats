#!/bin/bash
# This script rebuilds and restarts the Docker containers

# Exit immediately if a command exits with a non-zero status
set -e

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Cleaning up database files for consistent storage..."
./Application/backend/cleanup_databases.sh

echo "Making sure data directory is writable..."
chmod -R 777 "$SCRIPT_DIR/Application/backend/data"

echo "Testing database connection before rebuild..."
./Application/backend/test_database_connection.sh

echo "Rebuilding and restarting Docker containers..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "Waiting for backend container to start..."
sleep 10

# Check if the container is running
if ! docker-compose ps | grep -q "backend.*running"; then
    echo "ERROR: Backend container failed to start properly."
    echo "Checking container logs:"
    docker-compose logs backend
    exit 1
fi

echo "Running database migrations inside the container to ensure schema is up to date..."
if ! docker-compose exec backend python -m alembic upgrade head; then
    echo "WARNING: Alembic migrations failed. Attempting direct SQL fix..."
    docker-compose exec backend bash -c "sqlite3 /app/data/nba_stats.db 'ALTER TABLE data_update_status ADD COLUMN cancellation_requested BOOLEAN NOT NULL DEFAULT 0;'" || true
fi

# Verify migrations worked by checking for the column
echo "Verifying database schema..."
if ! docker-compose exec backend bash -c "sqlite3 /app/data/nba_stats.db 'SELECT cancellation_requested FROM data_update_status LIMIT 1;'" > /dev/null 2>&1; then
    echo "WARNING: Database schema verification failed. The column may still be missing."
    echo "Attempting a manual fix..."

    # Try a more direct approach - we run this again to be sure
    docker-compose exec backend bash -c "sqlite3 /app/data/nba_stats.db 'ALTER TABLE data_update_status ADD COLUMN cancellation_requested BOOLEAN NOT NULL DEFAULT 0;'" 2>/dev/null

    # Check again
    if ! docker-compose exec backend bash -c "sqlite3 /app/data/nba_stats.db 'SELECT cancellation_requested FROM data_update_status LIMIT 1;'" > /dev/null 2>&1; then
        echo "ERROR: Still couldn't fix the database schema."
        echo "Running the emergency fix script..."
        docker-compose exec backend bash -c "/app/emergency_column_fix.sh"

        # Final verification
        if ! docker-compose exec backend bash -c "sqlite3 /app/data/nba_stats.db 'SELECT cancellation_requested FROM data_update_status LIMIT 1;'" > /dev/null 2>&1; then
            echo "ERROR: All attempts to fix the schema failed."
            echo "You may need to run the recreate_database.sh script to completely rebuild the database."
            exit 1
        else
            echo "Emergency fix successful!"
        fi
    else
        echo "Manual fix successful!"
    fi
else
    echo "Database schema is correct!"
fi

# Test a basic API endpoint to make sure the application is working
echo "Testing API endpoint..."
if curl -s http://localhost:7778/status | grep -q "status"; then
    echo "API test successful! The application is running correctly."
else
    echo "WARNING: API endpoint test failed. The application may not be functioning correctly."
    echo "Check the logs for more information:"
    docker-compose logs backend
fi

echo "Docker containers have been rebuilt and restarted successfully."
echo "The application is now using the database in the Docker volume."
echo "Any data will persist between container restarts."
