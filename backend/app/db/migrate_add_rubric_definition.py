"""Migration script to add rubric_definition column to problems table."""

import asyncio
import json
import os
import sqlite3
from pathlib import Path

# Add rubric definitions for each problem based on the backend-revision-api.md spec


def get_rubric_definition(problem_id: str) -> list:
    """Generate rubric definition for each problem."""

    # Common rubric items that apply to most system design problems
    common_rubrics = {
        "url-shortener": [
            {
                "label": "Requirements Clarity",
                "description": "Identifies key constraints and asks clarifying questions",
                "phase_weights": {"clarify": 0.7, "estimate": 0.3}
            },
            {
                "label": "Capacity Estimation",
                "description": "Provides reasonable calculations for scale and storage",
                "phase_weights": {"estimate": 0.8, "design": 0.2}
            },
            {
                "label": "System Design",
                "description": "Proposes appropriate architecture with key components",
                "phase_weights": {"design": 0.9, "explain": 0.1}
            },
            {
                "label": "Scalability Plan",
                "description": "Addresses bottlenecks and scaling strategies",
                "phase_weights": {"design": 0.5, "explain": 0.5}
            },
            {
                "label": "Tradeoff Analysis",
                "description": "Explains key design choices and alternatives",
                "phase_weights": {"explain": 1.0}
            }
        ],
        "rate-limiter": [
            {
                "label": "Requirements Clarity",
                "description": "Identifies rate limiting algorithms and constraints",
                "phase_weights": {"clarify": 0.7, "estimate": 0.3}
            },
            {
                "label": "Capacity Estimation",
                "description": "Calculates throughput and memory requirements",
                "phase_weights": {"estimate": 0.8, "design": 0.2}
            },
            {
                "label": "System Design",
                "description": "Proposes distributed rate limiting architecture",
                "phase_weights": {"design": 0.9, "explain": 0.1}
            },
            {
                "label": "Distributed Coordination",
                "description": "Addresses consistency and coordination challenges",
                "phase_weights": {"design": 0.5, "explain": 0.5}
            },
            {
                "label": "Algorithm Selection",
                "description": "Justifies rate limiting algorithm choice and tradeoffs",
                "phase_weights": {"explain": 1.0}
            }
        ],
        "spotify": [
            {
                "label": "Requirements Clarity",
                "description": "Identifies streaming, catalog, and user activity requirements",
                "phase_weights": {"clarify": 0.7, "estimate": 0.3}
            },
            {
                "label": "Capacity Estimation",
                "description": "Estimates storage, bandwidth, and concurrent users",
                "phase_weights": {"estimate": 0.8, "design": 0.2}
            },
            {
                "label": "System Design",
                "description": "Proposes microservices architecture with CDN",
                "phase_weights": {"design": 0.9, "explain": 0.1}
            },
            {
                "label": "Data Architecture",
                "description": "Addresses storage, caching, and search strategies",
                "phase_weights": {"design": 0.6, "explain": 0.4}
            },
            {
                "label": "Streaming & CDN",
                "description": "Explains content delivery and reliability approach",
                "phase_weights": {"design": 0.4, "explain": 0.6}
            }
        ],
        "chat-system": [
            {
                "label": "Requirements Clarity",
                "description": "Identifies real-time delivery and consistency requirements",
                "phase_weights": {"clarify": 0.7, "estimate": 0.3}
            },
            {
                "label": "Capacity Estimation",
                "description": "Estimates message throughput and storage needs",
                "phase_weights": {"estimate": 0.8, "design": 0.2}
            },
            {
                "label": "System Design",
                "description": "Proposes WebSocket architecture with message queue",
                "phase_weights": {"design": 0.9, "explain": 0.1}
            },
            {
                "label": "Real-time Delivery",
                "description": "Addresses persistent connections and push notifications",
                "phase_weights": {"design": 0.5, "explain": 0.5}
            },
            {
                "label": "Consistency Model",
                "description": "Explains message ordering and read receipt tradeoffs",
                "phase_weights": {"explain": 1.0}
            }
        ],
        "youtube": [
            {
                "label": "Requirements Clarity",
                "description": "Identifies video pipeline and massive scale requirements",
                "phase_weights": {"clarify": 0.7, "estimate": 0.3}
            },
            {
                "label": "Capacity Estimation",
                "description": "Estimates storage, transcoding, and streaming capacity",
                "phase_weights": {"estimate": 0.8, "design": 0.2}
            },
            {
                "label": "System Design",
                "description": "Proposes comprehensive architecture with object storage and CDN",
                "phase_weights": {"design": 0.9, "explain": 0.1}
            },
            {
                "label": "Video Pipeline",
                "description": "Addresses upload, transcoding, and delivery flow",
                "phase_weights": {"design": 0.5, "explain": 0.5}
            },
            {
                "label": "Analytics & Scale",
                "description": "Explains view tracking and multi-region architecture",
                "phase_weights": {"design": 0.3, "explain": 0.7}
            }
        ],
        "google-docs": [
            {
                "label": "Requirements Clarity",
                "description": "Identifies collaborative editing and conflict resolution requirements",
                "phase_weights": {"clarify": 0.7, "estimate": 0.3}
            },
            {
                "label": "Capacity Estimation",
                "description": "Estimates concurrent editors and operation throughput",
                "phase_weights": {"estimate": 0.8, "design": 0.2}
            },
            {
                "label": "System Design",
                "description": "Proposes OT or CRDT-based architecture",
                "phase_weights": {"design": 0.9, "explain": 0.1}
            },
            {
                "label": "Conflict Resolution",
                "description": "Addresses operational transform or CRDT approach",
                "phase_weights": {"design": 0.5, "explain": 0.5}
            },
            {
                "label": "Consistency & Offline",
                "description": "Explains eventual consistency and offline editing strategy",
                "phase_weights": {"explain": 1.0}
            }
        ]
    }

    return common_rubrics.get(problem_id, [])


def main():
    """Run migration to add rubric_definition column."""
    # Get database path from environment or use default
    db_path = os.getenv("SQLITE_DB_PATH", "backend/data/designdual.db")
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"Database not found at {db_path}")
        print("Please run: uv run python -m app.db.init_db")
        return

    print(f"Migrating database at {db_path}...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(problems)")
        columns = [row[1] for row in cursor.fetchall()]

        if "rubric_definition" in columns:
            print("Column 'rubric_definition' already exists")
        else:
            # Add the column
            print("Adding rubric_definition column...")
            cursor.execute("""
                ALTER TABLE problems
                ADD COLUMN rubric_definition TEXT NOT NULL DEFAULT '[]'
                CHECK (json_valid(rubric_definition))
            """)
            conn.commit()
            print("✓ Column added successfully")

        # Update existing problems with rubric definitions
        print("\nUpdating problem rubric definitions...")
        cursor.execute("SELECT id FROM problems")
        problem_ids = [row[0] for row in cursor.fetchall()]

        for problem_id in problem_ids:
            rubric_def = get_rubric_definition(problem_id)
            rubric_json = json.dumps(rubric_def)

            cursor.execute(
                "UPDATE problems SET rubric_definition = ? WHERE id = ?",
                (rubric_json, problem_id)
            )
            print(f"✓ Updated {problem_id}: {len(rubric_def)} rubric items")

        conn.commit()
        print("\n✓ Migration completed successfully")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
