# NBA Stats Application Backend

## Overview

This backend provides a FastAPI-based API for NBA statistics data. It handles data collection, storage, and querying through RESTful endpoints.

## Database Management

### Database Location

The application uses SQLite for data storage. The database file is located at:

- Docker environment: `/app/data/nba_stats.db`
- Development environment: `./data/nba_stats.db`

The location is controlled by the environment variable `NBA_STATS_DATA_DIR`.

### Database Schema Management

Database schema is managed through Alembic migrations. These migrations are automatically applied:

1. During Docker container startup
2. When running `fix_database_schema.sh`
3. When the application detects missing schemas at runtime

### Utility Scripts

Several scripts are provided to manage the database:

| Script | Purpose |
|--------|---------|
| `cleanup_databases.sh` | Consolidates multiple database files into a single file in the correct location |
| `fix_database_schema.sh` | Applies Alembic migrations to fix schema issues |
| `fix_missing_column.sh` | Specifically fixes the "no column named cancellation_requested" error |
| `recreate_database.sh` | Last resort option to completely rebuild the database from scratch |

### Common Issues

#### Missing Column Error

If you encounter this error:
```
sqlite3.OperationalError: table data_update_status has no column named cancellation_requested
```

Run the emergency fix script:
```bash
./emergency_column_fix.sh
```

If that doesn't work, try these steps in order:

1. Direct SQL fix:
   ```bash
   sqlite3 ./data/nba_stats.db "ALTER TABLE data_update_status ADD COLUMN cancellation_requested BOOLEAN NOT NULL DEFAULT 0;"
   ```

2. Full schema fix:
   ```bash
   ./fix_database_schema.sh
   ```

3. Rebuild Docker container:
   ```bash
   cd .. && ./rebuild_docker.sh
   ```

4. Last resort - recreate database:
   ```bash
   ./recreate_database.sh
   ```

#### Data Not Persisting

If data isn't persisting between application restarts:

1. Check that the database is in `./data/nba_stats.db`
2. Run the cleanup script: `./cleanup_databases.sh`
3. Ensure proper permissions: `chmod -R 777 ./data`

## Development Setup

To set up a development environment:

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   cd .. && ./dev_with_correct_db.sh
   ```

## API Documentation

When the server is running, API documentation is available at:
- Swagger UI: `http://localhost:7778/docs`
- ReDoc: `http://localhost:7778/redoc`

## Testing

Run tests with:
```bash
pytest
```

## Docker Deployment

For Docker deployment, use:
```bash
cd .. && ./rebuild_docker.sh
```

This will rebuild the Docker containers and ensure the database is properly configured.

## Environment Variables

- `NBA_STATS_DATA_DIR`: Directory where the database is stored
- `NBA_STATS_DB_FILE`: Full path to the database file (takes precedence over DATA_DIR)
