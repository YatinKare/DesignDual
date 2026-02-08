"""Migration: Add v2 storage tables and columns for full contract compliance.

This migration adds:
1. submission_transcripts table for timestamped transcript storage
2. result_json column to submissions for caching final v2 results
3. completed_at column to submissions for completion timestamps
"""

import asyncio
import sqlite3
from pathlib import Path


def migrate_sync(db_path: str) -> None:
    """Add v2 storage tables and columns to existing database.

    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting v2 storage migration...")

        # 1. Add result_json column to submissions if it doesn't exist
        cursor.execute("PRAGMA table_info(submissions)")
        columns = [row[1] for row in cursor.fetchall()]

        if "result_json" not in columns:
            print("  Adding result_json column to submissions...")
            cursor.execute("""
                ALTER TABLE submissions
                ADD COLUMN result_json TEXT CHECK (result_json IS NULL OR json_valid(result_json))
            """)
            print("  ✓ Added result_json column")
        else:
            print("  ✓ result_json column already exists")

        # 2. Add completed_at column to submissions if it doesn't exist
        if "completed_at" not in columns:
            print("  Adding completed_at column to submissions...")
            cursor.execute("""
                ALTER TABLE submissions
                ADD COLUMN completed_at DATETIME
            """)
            print("  ✓ Added completed_at column")

            # Backfill completed_at for existing complete submissions
            cursor.execute("""
                UPDATE submissions
                SET completed_at = updated_at
                WHERE status = 'complete' AND completed_at IS NULL
            """)
            rows_updated = cursor.rowcount
            if rows_updated > 0:
                print(f"  ✓ Backfilled completed_at for {rows_updated} complete submissions")
        else:
            print("  ✓ completed_at column already exists")

        # 3. Create submission_transcripts table if it doesn't exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='submission_transcripts'"
        )
        if cursor.fetchone():
            print("  ✓ submission_transcripts table already exists")
        else:
            print("  Creating submission_transcripts table...")
            cursor.execute("""
                CREATE TABLE submission_transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id TEXT NOT NULL,
                    phase TEXT NOT NULL CHECK (
                        phase IN ('clarify', 'estimate', 'design', 'explain')
                    ),
                    timestamp_sec REAL NOT NULL CHECK (timestamp_sec >= 0.0),
                    text TEXT NOT NULL,
                    is_highlight BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE
                )
            """)
            print("  ✓ Created submission_transcripts table")

            # Create indexes for fast lookups
            cursor.execute("""
                CREATE INDEX idx_submission_transcripts_submission
                ON submission_transcripts(submission_id, phase, timestamp_sec)
            """)
            print("  ✓ Created index idx_submission_transcripts_submission")

            cursor.execute("""
                CREATE INDEX idx_submission_transcripts_highlights
                ON submission_transcripts(submission_id, is_highlight)
                WHERE is_highlight = 1
            """)
            print("  ✓ Created index idx_submission_transcripts_highlights")

        conn.commit()
        print("✓ Migration complete! All v2 storage structures are in place.")

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

    print(f"Running v2 storage migration on: {default_db}")
    asyncio.run(migrate_async(str(default_db)))
    print("\nAll v2 storage tables are ready!")
