#!/usr/bin/env bash
# Nightly Postgres backup: pg_dump -> S3. Runs on the EC2 instance from the
# bilance-backup systemd timer (see infra/README.md). Installed to
# /usr/local/bin/bilance-backup.sh; runs as root, so the AWS CLI uses the
# instance role (bilance-api-instance-role, policy backup-bucket-access).
set -euo pipefail

BUCKET="${BACKUP_BUCKET:-bilance-db-backups-01}"
CONTAINER="bilance-db"
DB_USER="bilance"
DB_NAME="bilance"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
INNER="/tmp/bilance-${STAMP}.dump"        # inside the database container
FILE="/var/tmp/bilance-${STAMP}.dump"     # on the instance, after copying out
KEY="daily/bilance-${STAMP}.dump"

cleanup() {
  rm -f "$FILE"
  docker exec "$CONTAINER" rm -f "$INNER" > /dev/null 2>&1 || true
}
trap cleanup EXIT

# Dump inside the container. Custom format is compressed and lets pg_restore
# restore selectively.
docker exec "$CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --format=custom -f "$INNER"

# A failed or empty dump must never be uploaded as if it were a backup.
if ! docker exec "$CONTAINER" test -s "$INNER"; then
  echo "backup failed: the dump is empty" >&2
  exit 1
fi

# Check that the dump is readable (this lists its contents, restores nothing).
docker exec "$CONTAINER" pg_restore --list "$INNER" > /dev/null

# Only now copy the verified file out and upload it. The AWS CLI and the IAM
# role are on the instance, not in the database container.
docker cp "${CONTAINER}:${INNER}" "$FILE"
aws s3 cp "$FILE" "s3://${BUCKET}/${KEY}" --sse AES256 --only-show-errors
echo "backup ok: s3://${BUCKET}/${KEY} ($(stat -c %s "$FILE") bytes)"
