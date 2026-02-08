#!/usr/bin/env python3
"""Migration: Add QUEUED and PROCESSING statuses to submissions table.

This migration updates the CHECK constraint on the status column to include
the new statuses required for the v2 lifecycle:
- OLD: received → transcribing → grading → complete/failed
- NEW: queued → processing → transcribing → grading → complete/failed
"""

import asyncio
import sqlite3
import sys
from pathlib import Path


async def migrate():
    """Add QUEUED and PROCESSING statuses to submissions.status CHECK constraint."""
    backend_dir = Path(__file__).parent.parent.parent
    db_path = backend_dir / "data" / "designdual.db"

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting migration: Add QUEUED and PROCESSING statuses...")

        # SQLite doesn't support ALTER COLUMN for CHECK constraints
        # So we need to:
        # 1. Create new table with updated CHECK constraint
        # 2. Copy data from old table
        # 3. Drop old table
        # 4. Rename new table

        # Step 1: Create new table with updated CHECK constraint
        print("Creating new submissions table with updated status constraint...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions_new (
                id TEXT PRIMARY KEY NOT NULL,
                problem_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(
                    status IN ('queued', 'processing', 'received', 'transcribing', 'grading', 'complete', 'failed')
                ) DEFAULT 'queued',
                phase_times TEXT NOT NULL CHECK(json_valid(phase_times)),
                phases TEXT NOT NULL CHECK(json_valid(phases)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (problem_id) REFERENCES problems(id)
            )
        """)

        # Step 2: Copy data from old table to new table
        # Map old 'received' status to new 'queued' status
        print("Copying data from old table (mapping 'received' → 'queued')...")
        cursor.execute("""
            INSERT INTO submissions_new (id, problem_id, status, phase_times, phases, created_at, updated_at)
            SELECT
                id,
                problem_id,
                CASE
                    WHEN status = 'received' THEN 'queued'
                    ELSE status
                END as status,
                phase_times,
                phases,
                created_at,
                updated_at
            FROM submissions
        """)

        rows_copied = cursor.rowcount
        print(f"✅ Copied {rows_copied} submissions (mapped 'received' → 'queued')")

        # Step 3: Drop old table
        print("Dropping old submissions table...")
        cursor.execute("DROP TABLE submissions")

        # Step 4: Rename new table
        print("Renaming submissions_new → submissions...")
        cursor.execute("ALTER TABLE submissions_new RENAME TO submissions")

        # Recreate indexes if any existed
        print("Creating index on problem_id...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_submissions_problem_id
            ON submissions(problem_id)
        """)

        conn.commit()
        print("✅ Migration completed successfully!")
        print(f"   - Updated status CHECK constraint to include 'queued' and 'processing'")
        print(f"   - Migrated {rows_copied} existing submissions")
        print(f"   - Old 'received' statuses converted to 'queued'")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
