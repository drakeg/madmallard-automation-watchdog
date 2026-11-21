#!/usr/bin/env python3
"""Safe SQLite backup and verification; never restores over a live database."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

REQUIRED_TABLES = {"events", "alerts", "notification_queue", "job_settings"}

def verify(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError("Backup file does not exist")
    # URI read-only mode avoids creating/modifying a file by mistake.
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError("SQLite integrity check failed")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing = REQUIRED_TABLES - tables
        if missing:
            raise ValueError("Missing required tables: " + ", ".join(sorted(missing)))
        stats = {t: db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in sorted(REQUIRED_TABLES)}
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "tables": stats, "bytes": path.stat().st_size}

def backup(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise ValueError("Source SQLite database does not exist")
    if source == destination:
        raise ValueError("Refusing to overwrite source database")
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError("Refusing to overwrite existing backup")
    fd, tempname = tempfile.mkstemp(prefix=".watchdog-backup-", suffix=".sqlite3", dir=destination.parent)
    os.close(fd)
    temp = Path(tempname)
    try:
        os.chmod(temp, 0o600)
        with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as input_db:
            with sqlite3.connect(temp) as output_db:
                input_db.backup(output_db)
        result = verify(temp)
        temp.replace(destination)
        return result
    finally:
        if temp.exists():
            temp.unlink()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["backup", "verify"])
    parser.add_argument("--source", type=Path, default=Path("/data/watchdog.sqlite3"))
    parser.add_argument("--output", type=Path, help="Destination for new backup (required for backup)")
    parser.add_argument("--file", type=Path, help="Existing backup file (required for verify)")
    args = parser.parse_args()
    try:
        if args.action == "backup":
            if args.output is None:
                parser.error("--output is required for backup")
            result = backup(args.source, args.output)
        else:
            if args.file is None:
                parser.error("--file is required for verify")
            result = verify(args.file)
    except (ValueError, OSError, sqlite3.Error) as exc:
        print("Backup operation failed:", exc, file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
