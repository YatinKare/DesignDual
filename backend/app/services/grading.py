"""Grading service helpers for assembling agent input payloads."""

from __future__ import annotations

import asyncio
import base64
import logging
from pathlib import Path
from typing import Any, Dict

import aiosqlite
from google.adk.runners import InMemoryRunner
from google.adk.sessions import BaseSessionService, Session
from google.genai import types

from app.agents import grading_pipeline
from app.db import BACKEND_DIR, REPO_ROOT
from app.models import GradingReport, PhaseName, SubmissionStatus
from app.services.database import get_db_connection
from app.services.problems import get_problem_by_id
from app.services.submissions import (
    get_submission_by_id,
    update_submission_status,
    update_submission_transcripts,
)
from app.services.transcription import transcribe_audio_files_parallel

PHASE_ORDER: tuple[PhaseName, ...] = (
    PhaseName.CLARIFY,
    PhaseName.ESTIMATE,
    PhaseName.DESIGN,
    PhaseName.EXPLAIN,
)
DEFAULT_ADK_APP_NAME = "designdual-grading"
LOGGER = logging.getLogger(__name__)

# Timeout settings for grading pipeline
GRADING_PIPELINE_TIMEOUT_SECONDS = 300  # 5 minutes max for entire agent pipeline
TRANSCRIPTION_TIMEOUT_SECONDS = 120  # 2 minutes max for audio transcription


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


def _normalize_agent_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw agent output to match GradingReport schema.

    Handles two mismatches between agent output and Pydantic model:
    1. Verdict is uppercase (HIRE) but enum expects lowercase (hire).
    2. Dimensions use sub-dimension keys (requirements_gathering, etc.)
       but the model expects 4 top-level keys (scoping, design, scale, tradeoff).
    """
    # Map sub-dimensions to their parent dimension
    SUB_TO_PARENT = {
        "requirements_gathering": "scoping",
        "capacity_estimation": "scoping",
        "high_level_architecture": "design",
        "component_selection": "design",
        "api_design": "design",
        "estimation_alignment": "scale",
        "bottleneck_analysis": "scale",
        "scaling_strategies": "scale",
        "cap_understanding": "tradeoff",
        "technology_tradeoffs": "tradeoff",
        "self_critique": "tradeoff",
    }

    # 1. Lowercase the verdict
    if "verdict" in data and isinstance(data["verdict"], str):
        data["verdict"] = data["verdict"].lower()
        # Map NO_HIRE -> no_hire etc. (already lowercased)

    # 2. Collapse sub-dimensions into parent dimensions
    raw_dims = data.get("dimensions", {})
    needs_collapse = any(key in SUB_TO_PARENT for key in raw_dims)

    if needs_collapse:
        parent_buckets: Dict[str, list] = {}
        for sub_key, sub_val in raw_dims.items():
            parent = SUB_TO_PARENT.get(sub_key, sub_key)
            parent_buckets.setdefault(parent, []).append(sub_val)

        collapsed: Dict[str, Any] = {}
        for parent, entries in parent_buckets.items():
            scores = [e.get("score", 0) for e in entries if isinstance(e, dict)]
            avg_score = sum(scores) / len(scores) if scores else 0
            all_strengths = []
            all_weaknesses = []
            feedbacks = []
            for e in entries:
                if isinstance(e, dict):
                    all_strengths.extend(e.get("strengths", []))
                    all_weaknesses.extend(e.get("weaknesses", []))
                    if e.get("feedback"):
                        feedbacks.append(e["feedback"])
            collapsed[parent] = {
                "score": round(avg_score, 1),
                "feedback": " ".join(feedbacks),
                "strengths": all_strengths,
                "weaknesses": all_weaknesses,
            }
        data["dimensions"] = collapsed

    return data


def _validate_agent_results(session_state: Dict[str, Any], submission_id: str) -> None:
    """Validate that all required agent results are present in session state.

    Args:
        session_state: The ADK session state dictionary.
        submission_id: Submission ID for logging purposes.

    Raises:
        ValueError: If any required agent result is missing or invalid.
    """
    required_results = ["scoping_result", "design_result", "scale_result", "tradeoff_result"]
    missing_results = [key for key in required_results if not session_state.get(key)]

    if missing_results:
        LOGGER.error(
            "Missing agent results for submission %s: %s",
            submission_id,
            ", ".join(missing_results),
        )
        raise ValueError(f"Agent pipeline produced incomplete results: missing {missing_results}")

    # Validate that each result is a dict (not None, not a string, etc.)
    for key in required_results:
        result = session_state.get(key)
        if not isinstance(result, dict):
            LOGGER.error(
                "Invalid agent result type for %s in submission %s: %s",
                key,
                submission_id,
                type(result).__name__,
            )
            raise ValueError(f"Agent result '{key}' is invalid: expected dict, got {type(result).__name__}")


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


def _format_pipeline_input(submission_bundle: Dict[str, Any]) -> str:
    """Format submission payload into a single input prompt for the pipeline."""
    problem = submission_bundle["problem"]
    phases = submission_bundle["phases"]

    sections = [
        f"# Problem: {problem['title']}",
        "",
        problem["prompt"],
        "",
        "---",
        "",
    ]

    for phase in phases:
        sections.extend(
            [
                f"## Phase: {phase['phase'].title()}",
                "",
                "### Transcript:",
                phase.get("transcript") or "",
                "",
                f"[Canvas image for {phase['phase']} phase attached]",
                "",
                "---",
                "",
            ]
        )

    return "\n".join(sections)


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


async def save_grading_result(
    connection: aiosqlite.Connection,
    submission_id: str,
    grading_report: GradingReport,
) -> None:
    """Store the grading result in the database.

    Args:
        connection: Active database connection.
        submission_id: ID of the submission being graded.
        grading_report: The final grading report from the agent pipeline.

    Raises:
        ValueError: If grading_report is invalid or submission_id doesn't exist.
    """
    import json

    # Convert the grading report to JSON for storage
    dimensions_json = json.dumps(
        {k.value: v.model_dump(mode="json") for k, v in grading_report.dimensions.items()}
    )
    top_improvements_json = json.dumps(grading_report.top_improvements)
    phase_observations_json = json.dumps(
        {k.value: v for k, v in grading_report.phase_observations.items()}
    )
    raw_report_json = grading_report.model_dump_json()

    await connection.execute(
        """
        INSERT INTO grading_results (
            submission_id,
            overall_score,
            verdict,
            verdict_display,
            dimensions,
            top_improvements,
            phase_observations,
            raw_report,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (submission_id) DO UPDATE SET
            overall_score = excluded.overall_score,
            verdict = excluded.verdict,
            verdict_display = excluded.verdict_display,
            dimensions = excluded.dimensions,
            top_improvements = excluded.top_improvements,
            phase_observations = excluded.phase_observations,
            raw_report = excluded.raw_report,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            submission_id,
            grading_report.overall_score,
            grading_report.verdict.value,
            grading_report.verdict_display,
            dimensions_json,
            top_improvements_json,
            phase_observations_json,
            raw_report_json,
        ),
    )
    await connection.commit()


async def get_grading_result(
    connection: aiosqlite.Connection,
    submission_id: str,
) -> GradingReport | None:
    """Retrieve the grading result for a submission.

    Args:
        connection: Active database connection.
        submission_id: ID of the submission.

    Returns:
        GradingReport if found, None otherwise.
    """
    import json

    cursor = await connection.execute(
        """
        SELECT raw_report
        FROM grading_results
        WHERE submission_id = ?
        """,
        (submission_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None

    return GradingReport.model_validate_json(row[0])


async def run_grading_pipeline_background(submission_id: str) -> None:
    """Run transcription + grading asynchronously for a submission.

    This function handles the complete grading lifecycle with comprehensive error handling:
    1. Transcription phase - converts audio to text
    2. Agent grading phase - runs multi-agent evaluation pipeline
    3. Result persistence - saves grading report to database

    Failures at any stage will mark the submission as FAILED and log detailed errors.
    """
    connection = await get_db_connection()
    runner = None
    session_user_id = None
    session_id_to_cleanup = None

    try:
        # Validate submission exists
        submission = await get_submission_by_id(connection, submission_id)
        if submission is None:
            LOGGER.error("Submission not found for background grading: %s", submission_id)
            return

        # Transition from QUEUED → PROCESSING
        await update_submission_status(
            connection,
            submission_id,
            SubmissionStatus.PROCESSING,
        )
        LOGGER.info("Started processing submission %s", submission_id)

        # Phase 1: Transcription
        try:
            await update_submission_status(
                connection,
                submission_id,
                SubmissionStatus.TRANSCRIBING,
            )

            audio_paths = [
                submission.phases.get(phase).audio_path if submission.phases.get(phase) else None
                for phase in PHASE_ORDER
            ]

            # Apply timeout to transcription
            try:
                transcripts = await asyncio.wait_for(
                    transcribe_audio_files_parallel(audio_paths),
                    timeout=TRANSCRIPTION_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                LOGGER.error(
                    "Transcription timed out after %d seconds for submission %s",
                    TRANSCRIPTION_TIMEOUT_SECONDS,
                    submission_id,
                )
                raise ValueError(
                    f"Audio transcription timed out after {TRANSCRIPTION_TIMEOUT_SECONDS} seconds"
                )

            transcript_map = {
                phase: transcripts[index] for index, phase in enumerate(PHASE_ORDER)
            }
            await update_submission_transcripts(connection, submission_id, transcript_map)
            LOGGER.info("Transcription completed for submission %s", submission_id)
        except Exception as e:
            LOGGER.exception("Transcription failed for submission %s", submission_id)
            raise ValueError(f"Audio transcription failed: {e}") from e

        # Phase 2: Grading pipeline execution
        try:
            await update_submission_status(connection, submission_id, SubmissionStatus.GRADING)

            submission_bundle = await build_submission_bundle(connection, submission_id)
            runner = InMemoryRunner(agent=grading_pipeline, app_name=DEFAULT_ADK_APP_NAME)
            user_id = f"submission-{submission_id}"
            session_user_id = user_id  # Track for cleanup
            session_id_to_cleanup = submission_id  # Track for cleanup

            # Initialize session with grading state
            session = await initialize_grading_session(
                session_service=runner.session_service,
                submission_bundle=submission_bundle,
                user_id=user_id,
                app_name=DEFAULT_ADK_APP_NAME,
                session_id=submission_id,
            )

            input_text = _format_pipeline_input(submission_bundle)
            user_content = types.Content(
                role="user",
                parts=[types.Part(text=input_text)],
            )

            # Run agent pipeline - this executes all agents sequentially/parallel
            event_count = 0
            try:
                # Wrap agent execution with timeout
                async def run_agent_pipeline():
                    nonlocal event_count
                    async for event in runner.run_async(
                        user_id=user_id,
                        session_id=session.id,
                        new_message=user_content,
                    ):
                        event_count += 1
                        # Log agent progress (events include agent completions, tool calls, etc.)
                        if hasattr(event, 'type'):
                            LOGGER.debug(
                                "Agent pipeline event %d for submission %s: %s",
                                event_count,
                                submission_id,
                                event.type,
                            )

                await asyncio.wait_for(
                    run_agent_pipeline(),
                    timeout=GRADING_PIPELINE_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                LOGGER.error(
                    "Agent pipeline timed out after %d seconds for submission %s (%d events processed)",
                    GRADING_PIPELINE_TIMEOUT_SECONDS,
                    submission_id,
                    event_count,
                )
                raise ValueError(
                    f"Agent pipeline timed out after {GRADING_PIPELINE_TIMEOUT_SECONDS} seconds"
                )
            except Exception as e:
                LOGGER.exception(
                    "Agent pipeline execution failed for submission %s after %d events",
                    submission_id,
                    event_count,
                )
                raise ValueError(f"Agent execution failed: {e}") from e

            LOGGER.info(
                "Agent pipeline completed for submission %s with %d events",
                submission_id,
                event_count,
            )

        except Exception as e:
            LOGGER.exception("Grading pipeline failed for submission %s", submission_id)
            raise ValueError(f"Grading pipeline failed: {e}") from e

        # Phase 3: Result extraction and persistence
        try:
            # Retrieve the final grading report from session state
            final_session = await runner.session_service.get_session(
                app_name=DEFAULT_ADK_APP_NAME,
                user_id=user_id,
                session_id=session.id,
            )

            if not final_session:
                raise ValueError("Session not found after agent pipeline completion")

            # Validate intermediate agent results before checking final report
            try:
                _validate_agent_results(final_session.state, submission_id)
            except ValueError as e:
                LOGGER.error(
                    "Intermediate agent validation failed for submission %s: %s",
                    submission_id,
                    e,
                )
                # Continue to check for final_report - synthesis agent may have still succeeded
                # even if intermediate results are malformed

            if not final_session.state.get("final_report"):
                # Log intermediate agent results for debugging
                LOGGER.error(
                    "No final_report in session state for submission %s. "
                    "Intermediate results: scoping=%s, design=%s, scale=%s, tradeoff=%s",
                    submission_id,
                    bool(final_session.state.get("scoping_result")),
                    bool(final_session.state.get("design_result")),
                    bool(final_session.state.get("scale_result")),
                    bool(final_session.state.get("tradeoff_result")),
                )
                raise ValueError("Agent pipeline completed but produced no final report")

            # Parse the final report into a GradingReport object.
            # ADK output_key stores the LLM response as a string, so we may
            # need to parse JSON first.
            final_report_data = final_session.state["final_report"]
            if isinstance(final_report_data, str):
                import json as _json
                import re as _re
                # Strip markdown code fences if present (```json ... ```)
                cleaned = _re.sub(r"^```(?:json)?\s*", "", final_report_data.strip())
                cleaned = _re.sub(r"\s*```$", "", cleaned)
                final_report_data = _json.loads(cleaned)

            # Normalize agent output to match our Pydantic schema:
            final_report_data = _normalize_agent_report(final_report_data)

            try:
                grading_report = GradingReport.model_validate(final_report_data)
            except Exception as e:
                LOGGER.exception(
                    "Invalid grading report structure for submission %s. Raw data: %s",
                    submission_id,
                    final_report_data,
                )
                raise ValueError(f"Grading report validation failed: {e}") from e

            # Save to database
            await save_grading_result(connection, submission_id, grading_report)
            LOGGER.info("Saved grading result for submission %s", submission_id)

        except Exception as e:
            LOGGER.exception("Result extraction/persistence failed for submission %s", submission_id)
            raise ValueError(f"Result persistence failed: {e}") from e

        # Mark submission as complete
        await update_submission_status(connection, submission_id, SubmissionStatus.COMPLETE)
        LOGGER.info("Grading completed successfully for submission %s", submission_id)

    except Exception as outer_exception:
        # Top-level error handler - catches all failures
        LOGGER.exception("Background grading failed for submission %s: %s", submission_id, outer_exception)
        try:
            await update_submission_status(connection, submission_id, SubmissionStatus.FAILED)
        except Exception as status_update_error:
            # Even if we can't update status, log the error
            LOGGER.exception(
                "Failed to update submission status to failed for %s: %s",
                submission_id,
                status_update_error,
            )
    finally:
        # Clean up ADK session if it was created
        if runner and session_user_id and session_id_to_cleanup:
            try:
                await delete_grading_session(
                    session_service=runner.session_service,
                    user_id=session_user_id,
                    session_id=session_id_to_cleanup,
                    app_name=DEFAULT_ADK_APP_NAME,
                )
                LOGGER.info("Cleaned up grading session for submission %s", submission_id)
            except Exception as cleanup_error:
                # Log but don't fail if cleanup fails
                LOGGER.warning(
                    "Failed to clean up grading session for submission %s: %s",
                    submission_id,
                    cleanup_error,
                )

        # Always clean up database connection
        await connection.close()


__all__ = [
    "build_submission_bundle",
    "build_grading_session_state",
    "initialize_grading_session",
    "delete_grading_session",
    "save_grading_result",
    "get_grading_result",
    "run_grading_pipeline_background",
    "PHASE_ORDER",
    "DEFAULT_ADK_APP_NAME",
]
