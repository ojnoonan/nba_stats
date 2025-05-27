# NBA Stats Database Directory

This directory is where all database files should be stored.

The actual database file (nba_stats.db) is not tracked in git, but this directory structure is preserved.

## Purpose

- **Docker Deployments**: This directory is mounted as a volume to persist data between container restarts
- **Development Environment**: Using this location ensures consistency between dev and production
- **Data Preservation**: Keeping the database here prevents data loss during deployments

## Important Notes

- DO NOT place database files in other locations as they will not be persisted when using Docker
- If you encounter database errors, use the utility scripts in the parent directory:
  - `fix_missing_column.sh` - Fixes the specific "no column named cancellation_requested" error
  - `fix_database_schema.sh` - Runs migrations to fix general schema issues
  - `recreate_database.sh` - Last resort to completely rebuild the database

## Permissions

This directory should have write permissions for the application. In Docker, the
permissions are set automatically. For local development, the `dev_with_correct_db.sh`
script sets the appropriate permissions.

## Troubleshooting

If you don't see your data persisting between application restarts, ensure:

1. You're running the application with the correct environment settings
2. The database file is being created in this directory
3. There are no permission issues preventing writes
