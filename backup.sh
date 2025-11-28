#!/bin/bash
# Backup PostgreSQL database

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER="telegram-bot-db"
DB_NAME="${DB_NAME:-mydatabase}"
DB_USER="${DB_USER:-botuser}"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${TIMESTAMP}.sql"

echo "Starting backup..."
docker exec -t "$CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" \
    --clean --if-exists --create --encoding=UTF8 > "$BACKUP_FILE"

gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup completed: $BACKUP_FILE (Size: $SIZE)"

# Remove backups older than RETENTION_DAYS
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Done!"
