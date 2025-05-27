FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create data directory with proper permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Set environment variable to use the data directory
ENV NBA_STATS_DATA_DIR=/app/data

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Make sure alembic is directly available on PATH
RUN pip install alembic

# Create a startup script that runs migrations before starting the app
RUN echo '#!/bin/bash\n\
echo "Checking database schema..."\n\
\n\
# Check if we can query the database\n\
DB_FILE="/app/data/nba_stats.db"\n\
\n\
# Function to check and add a column if missing\n\
check_and_add_column() {\n\
    local table=$1\n\
    local column=$2\n\
    local type=$3\n\
    local default=$4\n\
    \n\
    if ! sqlite3 "$DB_FILE" "SELECT $column FROM $table LIMIT 1;" > /dev/null 2>&1; then\n\
        echo "Adding missing column: $column"\n\
        if [ -n "$default" ]; then\n\
            sqlite3 "$DB_FILE" "ALTER TABLE $table ADD COLUMN $column $type DEFAULT $default;"\n\
        else\n\
            sqlite3 "$DB_FILE" "ALTER TABLE $table ADD COLUMN $column $type;"\n\
        fi\n\
    fi\n\
}\n\
\n\
if [ -f "$DB_FILE" ]; then\n\
    echo "Database file exists, checking schema..."\n\
    \n\
    # First try migrations\n\
    cd /app && python -m alembic upgrade head\n\
    \n\
    # Then check and fix any missing columns\n\
    check_and_add_column "data_update_status" "cancellation_requested" "BOOLEAN" "0"\n\
    check_and_add_column "data_update_status" "teams_last_update" "DATETIME" "NULL"\n\
    check_and_add_column "data_update_status" "players_last_update" "DATETIME" "NULL"\n\
    check_and_add_column "data_update_status" "games_last_update" "DATETIME" "NULL"\n\
    check_and_add_column "data_update_status" "teams_percent_complete" "INTEGER" "0"\n\
    check_and_add_column "data_update_status" "players_percent_complete" "INTEGER" "0"\n\
    check_and_add_column "data_update_status" "games_percent_complete" "INTEGER" "0"\n\
    check_and_add_column "data_update_status" "current_detail" "TEXT" "NULL"\n\
    \n\
    echo "Schema verification complete"\n\
else\n\
    echo "No database file found, will be created on first run"\n\
    # Ensure directory is writable\n\
    chmod -R 777 /app/data\n\
fi\n\
\n\
echo "Starting application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 7778\n' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose the port the app runs on
EXPOSE 7778

# Command to run the application with migrations
CMD ["/app/start.sh"]
