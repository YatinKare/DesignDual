"""Submission creation and retrieval endpoints."""

from __future__ import annotations

import logging
import os
from typing import Dict, Optional

import aiosqlite
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.models import PhaseArtifacts, PhaseName, Submission
from app.models.contract_v2 import SubmissionResultV2
from app.services.artifacts import save_submission_artifacts_batch
from app.services.database import db_connection
from app.services.file_storage import get_file_storage_service
from app.services.grading import get_grading_result, run_grading_pipeline_background
from app.services.problems import get_problem_by_id
from app.services.result_transformer import build_submission_result_v2
from app.services.submissions import create_submission, get_submission_by_id

router = APIRouter(tags=["submissions"])
logger = logging.getLogger(__name__)


def _validate_canvas_file(canvas_file: UploadFile, phase_name: str) -> None:
    """Validate that a canvas file is non-empty and has correct type.

    Args:
        canvas_file: Uploaded canvas file
        phase_name: Name of the phase (for error messages)

    Raises:
        HTTPException: If file is empty or has invalid type
    """
    if canvas_file.size == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Canvas file for phase '{phase_name}' is empty",
        )

    # Check content type (expected to be image/png)
    if canvas_file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Canvas file for phase '{phase_name}' must be PNG or JPEG, got '{canvas_file.content_type}'",
        )


@router.post("/api/submissions", response_model=Dict[str, str])
async def create_submission_endpoint(
    background_tasks: BackgroundTasks,
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
    import json
    import uuid

    # Validate problem_id exists in database
    problem = await get_problem_by_id(connection, problem_id)
    if problem is None:
        raise HTTPException(
            status_code=404,
            detail=f"Problem with id '{problem_id}' not found",
        )

    # Parse phase_times JSON
    try:
        phase_times_dict = json.loads(phase_times)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid phase_times JSON: {e}",
        )

    # Validate phase_times has exactly the 4 required keys
    required_phases = {"clarify", "estimate", "design", "explain"}
    provided_phases = set(phase_times_dict.keys())

    if provided_phases != required_phases:
        missing = required_phases - provided_phases
        extra = provided_phases - required_phases
        error_parts = []
        if missing:
            error_parts.append(f"missing phases: {sorted(missing)}")
        if extra:
            error_parts.append(f"unexpected phases: {sorted(extra)}")
        raise HTTPException(
            status_code=400,
            detail=f"phase_times must contain exactly [clarify, estimate, design, explain]. {', '.join(error_parts)}",
        )

    # Convert to typed dict with PhaseName enum
    try:
        phase_times_typed = {
            PhaseName(phase): seconds for phase, seconds in phase_times_dict.items()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid phase name in phase_times: {e}",
        )

    # Validate all canvas files are non-empty before processing
    canvas_validations = [
        (canvas_clarify, "clarify"),
        (canvas_estimate, "estimate"),
        (canvas_design, "design"),
        (canvas_explain, "explain"),
    ]
    for canvas_file, phase_name in canvas_validations:
        _validate_canvas_file(canvas_file, phase_name)

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
    # Also collect artifact URLs for the submission_artifacts table
    artifacts_batch: Dict[PhaseName, Dict[str, Optional[str]]] = {}

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

            # Convert paths to URLs for artifact table
            canvas_url = storage_service.path_to_url(canvas_path) if canvas_path else None
            audio_url = storage_service.path_to_url(audio_path) if audio_path else None

            artifacts_batch[phase_name] = {
                "canvas_url": canvas_url,
                "audio_url": audio_url,
                "canvas_mime_type": "image/png" if canvas_url else None,
                "audio_mime_type": "audio/webm" if audio_url else None,
            }

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

    # Persist artifacts to submission_artifacts table
    try:
        await save_submission_artifacts_batch(connection, submission_id, artifacts_batch)
    except Exception as e:
        # Log error but don't fail the request - artifacts are already in phases JSON
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to persist artifacts for submission {submission_id}: {e}")

    background_tasks.add_task(run_grading_pipeline_background, submission.id)

    return {"submission_id": submission.id}


@router.get("/api/submissions/{submission_id}", response_model=SubmissionResultV2)
async def get_submission_result(
    submission_id: str,
    connection: aiosqlite.Connection = Depends(db_connection),
) -> SubmissionResultV2:
    """Retrieve the complete grading result for a submission.

    Returns a SubmissionResultV2 payload conforming to the Screen 2 contract.
    This includes phase scores, evidence, rubric breakdown, radar chart,
    strengths/weaknesses, next attempt plan, and reference outline.

    Args:
        submission_id: ID of the submission
        connection: Database connection

    Returns:
        SubmissionResultV2 with complete grading details

    Raises:
        HTTPException: 404 if submission not found or not yet graded
    """
    # Fetch submission
    submission = await get_submission_by_id(connection, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=404,
            detail=f"Submission {submission_id} not found",
        )

    # Check if submission has been graded
    if submission.status.value not in ["complete", "failed"]:
        raise HTTPException(
            status_code=404,
            detail=f"Submission {submission_id} is still {submission.status.value}. Grading not complete yet.",
        )

    # Fetch grading result
    grading_report = await get_grading_result(connection, submission_id)
    if grading_report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Grading result for submission {submission_id} not found",
        )

    # Transform v1 grading report to v2 SubmissionResultV2
    try:
        result_v2 = await build_submission_result_v2(
            connection, submission, grading_report
        )
        return result_v2
    except Exception as e:
        logger.error(
            f"Failed to build SubmissionResultV2 for {submission_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to build submission result",
        )


__all__ = ["router"]
