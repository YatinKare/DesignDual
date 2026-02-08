"""Migration to add submission_artifacts table for v2 contract compliance."""

import asyncio
import sqlite3
from pathlib import Path


async def migrate():
    """Add submission_artifacts table and migrate existing data."""
    # Connect to database
    db_path = Path(__file__).parent.parent.parent / "data" / "designdual.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        print("Starting migration: add submission_artifacts table...")

        # Create submission_artifacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submission_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT NOT NULL,
                phase TEXT NOT NULL CHECK (
                    phase IN ('clarify', 'estimate', 'design', 'explain')
                ),
                canvas_url TEXT,
                audio_url TEXT,
                canvas_mime_type TEXT,
                audio_mime_type TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (submission_id) REFERENCES submissions (id) ON DELETE CASCADE,
                UNIQUE(submission_id, phase)
            )
        """)

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_submission_artifacts_submission
            ON submission_artifacts(submission_id)
        """)

        print("✓ Created submission_artifacts table")

        # Migrate existing data from submissions.phases JSON to submission_artifacts
        cursor.execute("SELECT id, phases FROM submissions WHERE phases != '{}'")
        submissions = cursor.fetchall()

        migrated_count = 0
        for submission_id, phases_json in submissions:
            import json

            try:
                phases = json.loads(phases_json)

                # Insert artifact records for each phase
                for phase, artifacts in phases.items():
                    if not artifacts:
                        continue

                    canvas_path = artifacts.get("canvas_path")
                    audio_path = artifacts.get("audio_path")

                    # Convert filesystem paths to URLs
                    # For local development, use file:// URLs or relative paths
                    # In production, these would be S3/CDN URLs
                    canvas_url = None
                    audio_url = None

                    if canvas_path:
                        # Convert path to URL format
                        # For hackathon, use relative URL that frontend can access
                        canvas_url = f"/uploads/{submission_id}/canvas_{phase}.png"

                    if audio_path:
                        audio_url = f"/uploads/{submission_id}/audio_{phase}.webm"

                    # Infer MIME types from file extensions
                    canvas_mime = "image/png" if canvas_url else None
                    audio_mime = "audio/webm" if audio_url else None

                    cursor.execute(
                        """
                        INSERT INTO submission_artifacts
                        (submission_id, phase, canvas_url, audio_url, canvas_mime_type, audio_mime_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(submission_id, phase) DO UPDATE SET
                            canvas_url = excluded.canvas_url,
                            audio_url = excluded.audio_url,
                            canvas_mime_type = excluded.canvas_mime_type,
                            audio_mime_type = excluded.audio_mime_type
                        """,
                        (
                            submission_id,
                            phase,
                            canvas_url,
                            audio_url,
                            canvas_mime,
                            audio_mime,
                        ),
                    )
                    migrated_count += 1

            except json.JSONDecodeError:
                print(f"  Warning: Could not parse phases JSON for submission {submission_id}")
                continue

        conn.commit()
        print(f"✓ Migrated {migrated_count} artifact records from {len(submissions)} submissions")

        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM submission_artifacts")
        artifact_count = cursor.fetchone()[0]
        print(f"✓ Total artifact records: {artifact_count}")

        print("\nMigration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
