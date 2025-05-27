# Database Management for NBA Stats App

## Overview

This document explains how the database management has been updated to ensure consistent storage of data across development and production environments.

## Problem

Previously, the application was creating multiple database files in various locations, which could lead to:
1. Loss of data when Docker containers were recreated
2. Confusion about which database was the "source of truth"
3. Inconsistent behavior between development and production environments
4. Schema inconsistencies causing application errors, such as the `sqlite3.OperationalError: table data_update_status has no column named cancellation_requested` error

## Solution

### Docker Environment

- The database is now stored in a Docker volume at `/app/data/nba_stats.db`
- This ensures data is preserved when containers are restarted or rebuilt
- The Docker Compose file and Dockerfile have been updated to set the NBA_STATS_DATA_DIR environment variable
- Alembic migrations run automatically on container startup to ensure schema is up to date
- There's now built-in schema verification on container startup to detect and fix issues

### Development Environment

- For local development, use the `dev_with_correct_db.sh` script instead of `dev.sh`
- This script sets up the environment to use the database at `Application/backend/data/nba_stats.db`
- The same location is mounted as a volume in Docker, ensuring consistency
- Database migrations are run automatically to ensure schema is up to date
- Schema verification ensures consistency between development and production

### Database Cleanup

- The `cleanup_databases.sh` script has been added to consolidate database files
- It finds any existing database and migrates it to the correct location
- Redundant database files are backed up and then removed

### Database Schema Management

- Alembic migrations are now run automatically on startup in both development and Docker environments
- This ensures the database schema stays in sync with the application code
- The application attempts to detect and fix schema issues at runtime
- Several utility scripts have been added to handle specific schema problems:
  - `fix_missing_column.sh` - Specifically fixes the missing `cancellation_requested` column
  - `fix_database_schema.sh` - Runs Alembic migrations to fix general schema issues
  - `recreate_database.sh` - A last resort option to completely rebuild the database

## Usage Instructions

### For Local Development

```bash
# Run the development environment with the correct database location
./dev_with_correct_db.sh
```

### For Docker Deployment

```bash
# Rebuild Docker containers and migrate any existing database data
./rebuild_docker.sh
```

### Manual Database Cleanup

```bash
# If you need to manually clean up database files
cd Application/backend
./cleanup_databases.sh
```

### Fixing Schema Issues

```bash
# If you specifically see the missing cancellation_requested column error
cd Application/backend
./fix_missing_column.sh

# For general schema issues
cd Application/backend
./fix_database_schema.sh

# As a last resort, if other fixes don't work
cd Application/backend
./recreate_database.sh  # Warning: This will rebuild the database from scratch
```

## Troubleshooting

### Missing Column Error

If you encounter this error:
```
sqlite3.OperationalError: table data_update_status has no column named cancellation_requested
```

This happens because the database schema is out of sync with the application code. To fix it:

1. Run the specific fix script:
   ```bash
   cd Application/backend
   ./fix_missing_column.sh
   ```

2. If that doesn't work, try rebuilding the Docker container:
   ```bash
   ./rebuild_docker.sh
   ```

3. As a last resort, recreate the database:
   ```bash
   cd Application/backend
   ./recreate_database.sh
   ```

### Data Not Persisting Between Container Restarts

If your data isn't being saved between container restarts:

1. Verify the database is using the correct location:
   ```bash
   docker-compose exec backend bash -c "echo \$NBA_STATS_DATA_DIR"
   ```
   It should output: `/app/data`

2. Check if the database file exists in the volume:
   ```bash
   docker-compose exec backend bash -c "ls -la /app/data"
   ```
   You should see `nba_stats.db` in the listing

3. Verify that the application is using this database file by checking the logs:
   ```bash
   docker-compose logs backend | grep "Using database at"
   ```

## Verifying Database Location

The application now logs the database location on startup. Look for a message like:

```
Using database at: /app/data/nba_stats.db
```

This confirms the application is using the correct database file.

## Database Structure and Files

- `nba_stats.db` - The main database file containing all application data
- `alembic/versions/` - Contains database migration files
- `alembic/versions/57f5b3644f4a_add_cancellation_requested_to_.py` - The specific migration that adds the `cancellation_requested` column

## Development Best Practices

1. **Always use the proper scripts**:
   - Use `dev_with_correct_db.sh` for development
   - Use `rebuild_docker.sh` for rebuilding Docker containers

2. **When creating new database models**:
   - Always create a migration using Alembic: `alembic revision --autogenerate -m "description"`
   - Test migrations in both development and Docker environments
   - Update documentation if significant changes are made

3. **When changing database structure**:
   - Never make manual changes to the database schema
   - Always use Alembic migrations
   - Test thoroughly to ensure compatibility with existing data

## Security Considerations

- The data directory permissions have been set to be writable by the application
- In production environments, consider setting more restrictive permissions
- Database files are excluded from Git via `.gitignore` to prevent accidental commits
