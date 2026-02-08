"""Migration: Add grading_events table for SSE event persistence and replay.

This migration adds the grading_events table to store all status transitions
during the grading process, enabling SSE replay and recovery.
"""

import asyncio
import sqlite3
from pathlib import Path


def migrate_sync(db_path: str) -> None:
    """Add grading_events table to existing database.

    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table already exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='grading_events'"
        )
        if cursor.fetchone():
            print("✓ grading_events table already exists, skipping migration")
            return

        # Create grading_events table
        cursor.execute("""
            CREATE TABLE grading_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN (
                        'queued', 'processing', 'transcribing',
                        'clarify', 'estimate', 'design', 'explain',
                        'synthesizing', 'complete', 'failed'
                    )
                ),
                message TEXT NOT NULL,
                phase TEXT CHECK (
                    phase IS NULL OR phase IN ('clarify', 'estimate', 'design', 'explain')
                ),
                progress REAL CHECK (progress IS NULL OR (progress >= 0.0 AND progress <= 1.0)),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE
            )
        """)

        # Create index for fast lookup by submission
        cursor.execute("""
            CREATE INDEX idx_grading_events_submission
            ON grading_events(submission_id, created_at)
        """)

        conn.commit()
        print("✓ Created grading_events table with indexes")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


async def migrate_async(db_path: str) -> None:
    """Async wrapper for migration."""
    migrate_sync(db_path)


if __name__ == "__main__":
    # Default to development database
    repo_root = Path(__file__).parent.parent.parent.parent
    default_db = repo_root / "backend" / "data" / "designdual.db"

    print(f"Running migration on: {default_db}")
    asyncio.run(migrate_async(str(default_db)))
    print("Migration complete!")
