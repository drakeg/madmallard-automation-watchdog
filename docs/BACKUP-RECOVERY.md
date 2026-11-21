# SQLite backup and recovery

The Watchdog stores events, alerts, delivery attempts, and schedule settings in an isolated SQLite volume.

## Online backup

Copy the backup utility into the existing container using `docker compose cp scripts/backup.py watchdog:/tmp/watchdog-backup.py`. Then run:

```sh
docker compose exec -T watchdog python /tmp/watchdog-backup.py backup --source /data/watchdog.sqlite3 --output /data/watchdog-backup.sqlite3
```

Use a unique backup filename each time. The tool never overwrites existing files or the source. It uses SQLite's online backup API, verifies integrity and tables, and atomically commits the backup.

## Verify

```sh
docker compose exec -T watchdog python /tmp/watchdog-backup.py verify --file /data/watchdog-backup.sqlite3
```

Test a restore only into a **separate, isolated database** and confirm tables and row counts. This tool intentionally does not support destructive in-place restore.

## Recovery procedure

During an approved maintenance window, keep the original watchdog volume intact. Provision an independent replacement instance with matching protected configuration, transfer an encrypted verified backup securely into the replacement volume, and test admin login, schedules, active alerts and notification queue before switching over. Never run `docker compose down -v`. Only one production monitor should send notifications.

Backups include potentially sensitive operational information. Configure secure off-host backup, encryption, access controls, retention and recovery ownership with each customer before production use.
