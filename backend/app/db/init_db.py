"""Initialize the DesignDual SQLite database with the base schema."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

if __package__ in (None, ""):
    # When executed as a script (`python app/db/init_db.py`), ensure the backend
    # directory is on sys.path so `app.db` imports work consistently.
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from app.db import DEFAULT_DATABASE_URL, resolve_database_path
else:  # pragma: no cover - exercised when running as module
    from . import DEFAULT_DATABASE_URL, resolve_database_path

SCHEMA_FILENAME = Path(__file__).with_name("schema.sql")


def ensure_schema_exists(connection: sqlite3.Connection) -> None:
    """Verify all expected tables exist after schema execution."""

    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    tables = {row[0] for row in rows}
    required = {"problems", "submissions", "grading_results"}
    missing = required - tables
    if missing:  # pragma: no cover - schema mismatch guard
        formatted = ", ".join(sorted(missing))
        raise RuntimeError(f"Schema initialization incomplete, missing: {formatted}")


def init_database(database_url: str, schema_path: Path = SCHEMA_FILENAME) -> Path:
    """Create parent directories, apply schema, and return db path."""

    db_path = resolve_database_path(database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = schema_path.read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        ensure_schema_exists(conn)

    return db_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the SQLite database with the base schema."
    )
    parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help=(
            "sqlite connection string (default: %(default)s). "
            "Only sqlite:/// or sqlite+aiosqlite:/// URLs are supported."
        ),
    )
    parser.add_argument(
        "--schema",
        default=str(SCHEMA_FILENAME),
        help="Path to schema.sql (default: %(default)s).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    schema_path = Path(args.schema).resolve()
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    db_path = init_database(args.database_url, schema_path)
    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    main()
