"""Service layer helpers for the backend."""

from .database import db_connection, get_db_connection
from .grading import (
    build_grading_session_state,
    build_submission_bundle,
    delete_grading_session,
    initialize_grading_session,
)
from .problems import list_problem_summaries
from .submissions import (
    create_submission,
    get_submission_by_id,
    update_submission_transcripts,
    update_submission_status,
)
from .transcription import (
    transcribe_audio,
    transcribe_audio_bytes,
    transcribe_audio_files_parallel,
    is_supported_audio_format,
)

__all__ = [
    "db_connection",
    "get_db_connection",
    "build_grading_session_state",
    "build_submission_bundle",
    "initialize_grading_session",
    "delete_grading_session",
    "list_problem_summaries",
    "create_submission",
    "get_submission_by_id",
    "update_submission_transcripts",
    "update_submission_status",
    "transcribe_audio",
    "transcribe_audio_bytes",
    "transcribe_audio_files_parallel",
    "is_supported_audio_format",
]

