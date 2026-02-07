"""Grading service helpers for assembling agent input payloads."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict

import aiosqlite
from google.adk.sessions import BaseSessionService, Session

from app.db import BACKEND_DIR, REPO_ROOT
from app.models import PhaseName
from app.services.problems import get_problem_by_id
from app.services.submissions import get_submission_by_id

PHASE_ORDER: tuple[PhaseName, ...] = (
    PhaseName.CLARIFY,
    PhaseName.ESTIMATE,
    PhaseName.DESIGN,
    PhaseName.EXPLAIN,
)
DEFAULT_ADK_APP_NAME = "designdual-grading"


def _resolve_artifact_path(path_value: str) -> Path:
    """Resolve a stored artifact path into an existing filesystem path."""
    raw_path = Path(path_value).expanduser()
    candidates: list[Path]

    if raw_path.is_absolute():
        candidates = [raw_path]
    else:
        candidates = [
            (Path.cwd() / raw_path),
            (REPO_ROOT / raw_path),
            (BACKEND_DIR / raw_path),
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(f"Artifact file not found for stored path '{path_value}'")


def _read_file_as_base64(file_path: Path) -> str:
    """Read a binary file and return base64-encoded text."""
    return base64.b64encode(file_path.read_bytes()).decode("utf-8")


async def build_submission_bundle(
    connection: aiosqlite.Connection,
    submission_id: str,
) -> Dict[str, Any]:
    """Assemble a grading submission bundle from persisted problem/submission data.

    Args:
        connection: Active database connection.
        submission_id: Submission ID to assemble.

    Returns:
        Dictionary payload containing problem metadata, phase timing, and per-phase artifacts.

    Raises:
        ValueError: If submission/problem is missing or required phase artifacts are incomplete.
        FileNotFoundError: If a stored artifact path points to a missing file.
    """
    submission = await get_submission_by_id(connection, submission_id)
    if submission is None:
        raise ValueError(f"Submission '{submission_id}' not found")

    problem = await get_problem_by_id(connection, submission.problem_id)
    if problem is None:
        raise ValueError(
            f"Problem '{submission.problem_id}' not found for submission '{submission_id}'"
        )

    phases_payload: list[Dict[str, Any]] = []
    for phase in PHASE_ORDER:
        phase_artifacts = submission.phases.get(phase)
        if phase_artifacts is None:
            raise ValueError(
                f"Submission '{submission_id}' is missing artifacts for phase '{phase.value}'"
            )
        if not phase_artifacts.canvas_path:
            raise ValueError(
                f"Submission '{submission_id}' is missing canvas path for phase '{phase.value}'"
            )

        canvas_path = _resolve_artifact_path(phase_artifacts.canvas_path)
        phases_payload.append(
            {
                "phase": phase.value,
                "canvas_base64": _read_file_as_base64(canvas_path),
                "transcript": phase_artifacts.transcript,
                "transcript_language": phase_artifacts.transcript_language,
                "audio_path": phase_artifacts.audio_path,
            }
        )

    return {
        "submission_id": submission.id,
        "problem": problem.model_dump(mode="json"),
        "phase_times": {
            phase_name.value: seconds
            for phase_name, seconds in submission.phase_times.items()
        },
        "phases": phases_payload,
    }


def build_grading_session_state(
    submission_bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """Build initial ADK session state from a submission bundle."""
    return {
        "submission_id": submission_bundle["submission_id"],
        "problem": submission_bundle["problem"],
        "phase_times": submission_bundle["phase_times"],
        "phases": submission_bundle["phases"],
        # Pre-seed expected agent output slots.
        "scoping_result": None,
        "design_result": None,
        "scale_result": None,
        "tradeoff_result": None,
        "final_report": None,
    }


async def initialize_grading_session(
    session_service: BaseSessionService,
    submission_bundle: Dict[str, Any],
    user_id: str,
    app_name: str = DEFAULT_ADK_APP_NAME,
    session_id: str | None = None,
) -> Session:
    """Create an ADK session initialized with grading state from submission data."""
    resolved_session_id = session_id or str(submission_bundle["submission_id"])
    return await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=resolved_session_id,
        state=build_grading_session_state(submission_bundle),
    )


async def delete_grading_session(
    session_service: BaseSessionService,
    user_id: str,
    session_id: str,
    app_name: str = DEFAULT_ADK_APP_NAME,
) -> bool:
    """Delete a grading session if it exists.

    Returns:
        True when a session was deleted, False when no matching session existed.
    """
    existing = await session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if existing is None:
        return False

    await session_service.delete_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    return True


__all__ = [
    "build_submission_bundle",
    "build_grading_session_state",
    "initialize_grading_session",
    "delete_grading_session",
    "PHASE_ORDER",
    "DEFAULT_ADK_APP_NAME",
]
