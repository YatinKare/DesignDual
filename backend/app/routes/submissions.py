"""Submission creation and retrieval endpoints."""

from __future__ import annotations

import os
from typing import Dict, Optional

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models import PhaseArtifacts, PhaseName, Submission
from app.services.database import db_connection
from app.services.file_storage import get_file_storage_service
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
    # TODO: Validate problem_id exists

    import json
    import uuid

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

    # Generate submission ID before saving files
    submission_id = str(uuid.uuid4())

    # Initialize file storage service (get upload root and size limit from environment at runtime)
    upload_root = os.getenv("UPLOAD_ROOT", "./storage/uploads")
    max_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    storage_service = get_file_storage_service(upload_root, max_size_mb)

    # Save canvas files (required)
    canvas_files = {
        PhaseName.CLARIFY: canvas_clarify,
        PhaseName.ESTIMATE: canvas_estimate,
        PhaseName.DESIGN: canvas_design,
        PhaseName.EXPLAIN: canvas_explain,
    }

    # Save audio files (optional)
    audio_files = {
        PhaseName.CLARIFY: audio_clarify,
        PhaseName.ESTIMATE: audio_estimate,
        PhaseName.DESIGN: audio_design,
        PhaseName.EXPLAIN: audio_explain,
    }

    # Build phases dictionary with file paths
    phases_dict: Dict[PhaseName, PhaseArtifacts] = {}

    try:
        for phase_name in [
            PhaseName.CLARIFY,
            PhaseName.ESTIMATE,
            PhaseName.DESIGN,
            PhaseName.EXPLAIN,
        ]:
            # Save canvas (required)
            canvas_path = await storage_service.save_canvas(
                canvas_files[phase_name],
                submission_id,
                phase_name.value,
            )

            # Save audio (optional)
            audio_path = await storage_service.save_audio(
                audio_files[phase_name],
                submission_id,
                phase_name.value,
            )

            phases_dict[phase_name] = PhaseArtifacts(
                canvas_path=canvas_path,
                audio_path=audio_path,
            )

    except IOError as e:
        # If any file save fails, cleanup and raise error
        storage_service.delete_submission_files(submission_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded files: {e}",
        )

    # Create submission record with file paths
    submission = await create_submission(
        connection=connection,
        problem_id=problem_id,
        phase_times=phase_times_typed,
        phases=phases_dict,
        submission_id=submission_id,
    )

    return {"submission_id": submission.id}


__all__ = ["router"]
