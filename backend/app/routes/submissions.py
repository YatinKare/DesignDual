"""Submission creation and retrieval endpoints."""

from __future__ import annotations

from typing import Dict, Optional

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models import PhaseArtifacts, PhaseName, Submission
from app.services.database import db_connection
from app.services.submissions import create_submission

router = APIRouter(tags=["submissions"])


@router.post("/api/submissions", response_model=Dict[str, str])
async def create_submission_endpoint(
    problem_id: str = Form(...),
    canvas_clarify: UploadFile = File(...),
    canvas_estimate: UploadFile = File(...),
    canvas_design: UploadFile = File(...),
    canvas_explain: UploadFile = File(...),
    audio_clarify: Optional[UploadFile] = File(None),
    audio_estimate: Optional[UploadFile] = File(None),
    audio_design: Optional[UploadFile] = File(None),
    audio_explain: Optional[UploadFile] = File(None),
    phase_times: str = Form(...),  # JSON string: {"clarify": 300, "estimate": 180, ...}
    connection: aiosqlite.Connection = Depends(db_connection),
) -> Dict[str, str]:
    """Create a new submission from uploaded canvas snapshots and audio files.

    Args:
        problem_id: ID of the problem being solved
        canvas_clarify: PNG snapshot from clarify phase
        canvas_estimate: PNG snapshot from estimate phase
        canvas_design: PNG snapshot from design phase
        canvas_explain: PNG snapshot from explain phase
        audio_clarify: Optional audio recording from clarify phase
        audio_estimate: Optional audio recording from estimate phase
        audio_design: Optional audio recording from design phase
        audio_explain: Optional audio recording from explain phase
        phase_times: JSON string with elapsed time (seconds) per phase
        connection: Database connection

    Returns:
        Dictionary with submission_id
    """
    # TODO: Validate problem_id exists (will be done in task 2.3)
    # TODO: Validate file types and sizes (will be done in task 2.4)
    # TODO: Save files to disk (will be done in task 2.2)

    import json

    # Parse phase_times JSON
    try:
        phase_times_dict = json.loads(phase_times)
        phase_times_typed = {
            PhaseName(phase): seconds for phase, seconds in phase_times_dict.items()
        }
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid phase_times format: {e}",
        )

    # For now, create placeholder PhaseArtifacts (file saving will be done in task 2.2)
    phases_dict: Dict[PhaseName, PhaseArtifacts] = {
        PhaseName.CLARIFY: PhaseArtifacts(
            canvas_path=None,  # Will be set in task 2.2
            audio_path=None,
        ),
        PhaseName.ESTIMATE: PhaseArtifacts(
            canvas_path=None,
            audio_path=None,
        ),
        PhaseName.DESIGN: PhaseArtifacts(
            canvas_path=None,
            audio_path=None,
        ),
        PhaseName.EXPLAIN: PhaseArtifacts(
            canvas_path=None,
            audio_path=None,
        ),
    }

    # Create submission record
    submission = await create_submission(
        connection=connection,
        problem_id=problem_id,
        phase_times=phase_times_typed,
        phases=phases_dict,
    )

    return {"submission_id": submission.id}


__all__ = ["router"]
