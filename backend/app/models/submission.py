"""Submission schemas describing stored artifacts and grading state."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional

from pydantic import Field

from .common import APISchema, PhaseName, SubmissionStatus

if TYPE_CHECKING:  # pragma: no cover - import only for typing
    from .grading import GradingReport


class PhaseArtifacts(APISchema):
    """Paths and derived data captured per phase."""

    canvas_path: Optional[str] = Field(
        default=None, description="Filesystem path to the PNG snapshot."
    )
    audio_path: Optional[str] = Field(
        default=None, description="Filesystem path to the recorded audio clip."
    )
    transcript: Optional[str] = Field(
        default=None,
        description="Transcript text returned by the transcription service.",
    )
    transcript_language: Optional[str] = Field(
        default=None, description="BCP-47 language tag returned by Gemini."
    )


class Submission(APISchema):
    """Primary submission record surfaced via API endpoints."""

    id: str
    problem_id: str
    status: SubmissionStatus = SubmissionStatus.QUEUED
    created_at: datetime
    updated_at: datetime
    phase_times: Dict[PhaseName, int] = Field(
        default_factory=dict,
        description="Client-supplied elapsed time (seconds) spent in each phase.",
    )
    phases: Dict[PhaseName, PhaseArtifacts] = Field(
        default_factory=dict,
        description="Map of per-phase artifact metadata and derived transcripts.",
    )
    grading_report: Optional["GradingReport"] = Field(
        default=None,
        description="Final grading payload once the agent pipeline finishes.",
    )


__all__ = ["PhaseArtifacts", "Submission"]
