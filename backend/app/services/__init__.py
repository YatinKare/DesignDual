"""Service layer helpers for the backend."""

from .artifacts import (
    get_submission_artifacts,
    save_submission_artifact,
    save_submission_artifacts_batch,
)
from .database import db_connection, get_db_connection
from .grading import (
    build_grading_session_state,
    build_submission_bundle,
    delete_grading_session,
    get_grading_result,
    initialize_grading_session,
    run_grading_pipeline_background,
    save_grading_result,
)
from .grading_events import (
    GradingEvent,
    get_grading_events,
    save_grading_event,
)
from .problems import list_problem_summaries
from .status_compat import (
    legacy_status_to_v2,
    normalize_status_input,
    v2_status_to_legacy,
)
from .result_transformer import build_submission_result_v2
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
    "save_grading_result",
    "get_grading_result",
    "run_grading_pipeline_background",
    "list_problem_summaries",
    "create_submission",
    "get_submission_by_id",
    "update_submission_transcripts",
    "update_submission_status",
    "transcribe_audio",
    "transcribe_audio_bytes",
    "transcribe_audio_files_parallel",
    "is_supported_audio_format",
    "save_submission_artifact",
    "save_submission_artifacts_batch",
    "get_submission_artifacts",
    "build_submission_result_v2",
    "GradingEvent",
    "save_grading_event",
    "get_grading_events",
    "legacy_status_to_v2",
    "v2_status_to_legacy",
    "normalize_status_input",
]
