"""Transform v1 grading results into v2 SubmissionResultV2 format."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

import aiosqlite

from app.models import GradingReport, PhaseName, Submission
from app.models.contract_v2 import (
    EvidenceItem,
    NextAttemptItem,
    PhaseScore,
    ProblemMetadata,
    RadarDimension,
    ReferenceOutline,
    ReferenceOutlineSection,
    RubricItem,
    RubricStatus,
    StrengthWeakness,
    SubmissionResultV2,
    TranscriptSnippet,
)
from app.services.artifacts import get_submission_artifacts
from app.services.problems import get_problem_by_id

logger = logging.getLogger(__name__)

# Mapping from v1 dimensions to v2 phases (best effort compatibility)
DIMENSION_TO_PHASE_MAP = {
    "scoping": PhaseName.CLARIFY,  # Scoping primarily happens during clarify
    "design": PhaseName.DESIGN,  # Design is design
    "scale": PhaseName.ESTIMATE,  # Scale analysis relates to estimation
    "tradeoff": PhaseName.EXPLAIN,  # Tradeoff reasoning happens during explain
}


def _generate_phase_bullets(dimension_name: str, dimension_data: Any) -> List[str]:
    """Generate 3-6 feedback bullets from v1 dimension feedback.

    Args:
        dimension_name: Name of the dimension (scoping, design, scale, tradeoff)
        dimension_data: DimensionScore model with score, feedback, strengths, weaknesses

    Returns:
        List of 3-6 concise feedback bullets
    """
    from app.models import DimensionScore

    bullets = []

    # Handle both DimensionScore models and dicts for compatibility
    if isinstance(dimension_data, DimensionScore):
        strengths = dimension_data.strengths
        weaknesses = dimension_data.weaknesses
        feedback = dimension_data.feedback
    else:
        strengths = dimension_data.get("strengths", [])
        weaknesses = dimension_data.get("weaknesses", [])
        feedback = dimension_data.get("feedback", "")

    # Add strengths (if present)
    if strengths:
        for strength in strengths[:2]:  # Max 2 strengths
            bullets.append(f"✓ {strength}")

    # Add weaknesses (if present)
    if weaknesses:
        for weakness in weaknesses[:2]:  # Max 2 weaknesses
            bullets.append(f"✗ {weakness}")

    # If we have less than 3 bullets, add the general feedback
    if len(bullets) < 3 and feedback:
        if isinstance(feedback, str):
            # Split feedback into sentences and take first few
            sentences = [s.strip() for s in feedback.split(".") if s.strip()]
            for sentence in sentences[: 6 - len(bullets)]:
                if sentence and sentence not in bullets:
                    bullets.append(sentence)

    # Ensure we have at least 3 bullets
    while len(bullets) < 3:
        bullets.append(f"{dimension_name.title()} assessment in progress")

    # Cap at 6 bullets
    return bullets[:6]


def _generate_evidence_items(
    artifacts: Dict[str, Dict[str, Any]]
) -> List[EvidenceItem]:
    """Generate exactly 4 evidence items from submission artifacts.

    Args:
        artifacts: Dict mapping phase name to artifact URLs

    Returns:
        List of exactly 4 EvidenceItem objects
    """
    evidence = []
    phase_order = ["clarify", "estimate", "design", "explain"]

    for phase_str in phase_order:
        phase = PhaseName(phase_str)
        artifact = artifacts.get(phase_str, {})
        canvas_url = artifact.get("canvas_url", f"/uploads/missing/{phase_str}.png")

        # Create evidence item with empty transcripts for now (v1 doesn't have timestamped transcripts)
        evidence.append(
            EvidenceItem(
                phase=phase,
                snapshot_url=canvas_url,
                transcripts=[],  # v1 compatibility: no timestamped transcripts
                noticed=None,  # v1 compatibility: no per-phase notices
            )
        )

    return evidence


def _generate_phase_scores(grading_report: GradingReport) -> List[PhaseScore]:
    """Generate exactly 4 phase scores from v1 dimension scores.

    Maps v1 dimensions (scoping, design, scale, tradeoff) to v2 phases.

    Args:
        grading_report: v1 GradingReport with dimension scores

    Returns:
        List of exactly 4 PhaseScore objects
    """
    from app.models import DimensionScore

    phase_scores = []

    for dimension_name, phase in DIMENSION_TO_PHASE_MAP.items():
        dimension_data = grading_report.dimensions.get(dimension_name)
        if dimension_data is None:
            # Create a default DimensionScore if missing
            score = 5.0
            bullets = [f"{dimension_name.title()} assessment pending"]
        else:
            # Extract score from DimensionScore model
            if isinstance(dimension_data, DimensionScore):
                score = dimension_data.score
            else:
                score = dimension_data.get("score", 5.0)
            bullets = _generate_phase_bullets(dimension_name, dimension_data)

        phase_scores.append(PhaseScore(phase=phase, score=score, bullets=bullets))

    return phase_scores


def _generate_rubric_items(
    grading_report: GradingReport, problem_rubric: List[Any]
) -> List[RubricItem]:
    """Generate rubric items with scores derived from phase scores.

    Args:
        grading_report: v1 GradingReport
        problem_rubric: Rubric definition from problem (list of RubricDefinition models)

    Returns:
        List of RubricItem objects
    """
    from app.models import DimensionScore, RubricDefinition

    rubric_items = []

    for rubric_def in problem_rubric:
        # Handle both RubricDefinition models and dicts
        if isinstance(rubric_def, RubricDefinition):
            label = rubric_def.label
            description = rubric_def.description
            phase_weights = rubric_def.phase_weights
        else:
            label = rubric_def.get("label", "Unknown Criterion")
            description = rubric_def.get("description", "")
            phase_weights = rubric_def.get("phase_weights", {})

        # Compute weighted average of dimension scores
        # Map phase weights to dimension scores using our compatibility mapping
        weighted_score = 0.0
        total_weight = 0.0

        for phase_str, weight in phase_weights.items():
            phase = PhaseName(phase_str)
            # Find which dimension maps to this phase
            dimension_name = next(
                (dim for dim, p in DIMENSION_TO_PHASE_MAP.items() if p == phase),
                "scoping",
            )
            dimension_data = grading_report.dimensions.get(dimension_name)
            if dimension_data is None:
                score = 5.0
            elif isinstance(dimension_data, DimensionScore):
                score = dimension_data.score
            else:
                score = dimension_data.get("score", 5.0)
            weighted_score += score * weight
            total_weight += weight

        final_score = weighted_score / total_weight if total_weight > 0 else 5.0

        # Determine status based on score thresholds
        if final_score >= 8.0:
            status = RubricStatus.PASS
        elif final_score >= 5.0:
            status = RubricStatus.PARTIAL
        else:
            status = RubricStatus.FAIL

        # Extract computed_from phases
        computed_from = [PhaseName(p) for p in phase_weights.keys()]

        rubric_items.append(
            RubricItem(
                label=label,
                description=description,
                score=round(final_score, 1),
                status=status,
                computed_from=computed_from,
            )
        )

    return rubric_items


def _generate_radar_dimensions(grading_report: GradingReport) -> List[RadarDimension]:
    """Generate radar dimensions from v1 dimension scores.

    Maps v1 dimensions to radar skills:
    - scoping → clarity (how clear is the problem understanding)
    - design → structure (how well-structured is the solution)
    - scale → power (how scalable is the design)
    - tradeoff → wisdom (how thoughtful are the tradeoffs)

    Args:
        grading_report: v1 GradingReport

    Returns:
        List of RadarDimension objects
    """
    from app.models import DimensionScore

    dimension_to_radar = {
        "scoping": ("clarity", "Clarity"),
        "design": ("structure", "Structure"),
        "scale": ("power", "Power"),
        "tradeoff": ("wisdom", "Wisdom"),
    }

    radar = []
    for dimension_name, (skill, label) in dimension_to_radar.items():
        dimension_data = grading_report.dimensions.get(dimension_name)
        if dimension_data is None:
            score = 5.0
        elif isinstance(dimension_data, DimensionScore):
            score = dimension_data.score
        else:
            score = dimension_data.get("score", 5.0)
        radar.append(RadarDimension(skill=skill, score=score, label=label))

    return radar


def _generate_strengths_weaknesses(
    grading_report: GradingReport,
) -> tuple[List[StrengthWeakness], List[StrengthWeakness]]:
    """Extract strengths and weaknesses from v1 dimensions.

    Args:
        grading_report: v1 GradingReport

    Returns:
        Tuple of (strengths, weaknesses) lists
    """
    from app.models import DimensionScore

    strengths = []
    weaknesses = []

    for dimension_name, phase in DIMENSION_TO_PHASE_MAP.items():
        dimension_data = grading_report.dimensions.get(dimension_name)
        if dimension_data is None:
            continue

        # Handle DimensionScore models
        if isinstance(dimension_data, DimensionScore):
            strength_list = dimension_data.strengths
            weakness_list = dimension_data.weaknesses
        else:
            strength_list = dimension_data.get("strengths", [])
            weakness_list = dimension_data.get("weaknesses", [])

        # Extract strengths
        for strength_text in strength_list:
            strengths.append(
                StrengthWeakness(
                    phase=phase,
                    text=strength_text,
                    timestamp_sec=None,  # v1 doesn't have timestamps
                )
            )

        # Extract weaknesses
        for weakness_text in weakness_list:
            weaknesses.append(
                StrengthWeakness(
                    phase=phase,
                    text=weakness_text,
                    timestamp_sec=None,  # v1 doesn't have timestamps
                )
            )

    return strengths, weaknesses


def _generate_next_attempt_plan(
    grading_report: GradingReport,
) -> List[NextAttemptItem]:
    """Generate next attempt plan from v1 top improvements.

    Args:
        grading_report: v1 GradingReport

    Returns:
        List of at least 3 NextAttemptItem objects
    """
    plan = []

    for improvement in grading_report.top_improvements[:5]:  # Take up to 5
        plan.append(
            NextAttemptItem(
                what_went_wrong=improvement,
                do_next_time=f"Focus on: {improvement.lower()}",
            )
        )

    # Ensure we have at least 3 items
    while len(plan) < 3:
        plan.append(
            NextAttemptItem(
                what_went_wrong="Additional improvement area to be identified",
                do_next_time="Review feedback and practice this dimension",
            )
        )

    return plan


def _generate_follow_up_questions() -> List[str]:
    """Generate at least 3 follow-up questions (v1 compatibility placeholder).

    Returns:
        List of at least 3 follow-up questions
    """
    return [
        "How would you handle traffic spikes 10x larger than your estimates?",
        "What monitoring and alerting would you put in place for this system?",
        "How would you evolve this design as requirements change over time?",
    ]


def _generate_reference_outline() -> ReferenceOutline:
    """Generate reference outline (v1 compatibility placeholder).

    Returns:
        ReferenceOutline with generic structure
    """
    return ReferenceOutline(
        sections=[
            ReferenceOutlineSection(
                section="Requirements & Scope",
                bullets=[
                    "Define functional requirements",
                    "Identify non-functional requirements (scale, latency, availability)",
                    "Clarify constraints and assumptions",
                ],
            ),
            ReferenceOutlineSection(
                section="Capacity Estimation",
                bullets=[
                    "Calculate traffic patterns (QPS, bandwidth)",
                    "Estimate storage requirements",
                    "Determine compute resource needs",
                ],
            ),
            ReferenceOutlineSection(
                section="High-Level Design",
                bullets=[
                    "Sketch system components",
                    "Define data flow",
                    "Identify key technologies",
                ],
            ),
            ReferenceOutlineSection(
                section="Deep Dive & Tradeoffs",
                bullets=[
                    "Discuss scaling strategies",
                    "Analyze consistency vs availability tradeoffs",
                    "Address failure scenarios",
                ],
            ),
        ]
    )


async def build_submission_result_v2(
    connection: aiosqlite.Connection,
    submission: Submission,
    grading_report: GradingReport,
) -> SubmissionResultV2:
    """Transform v1 grading data into v2 SubmissionResultV2 format.

    This is a compatibility layer that bridges the gap between v1 dimension-based
    grading and v2 phase-based grading. It maps v1 dimensions to v2 phases and
    generates the required v2 structures.

    Args:
        connection: Database connection
        submission: Submission record
        grading_report: v1 GradingReport

    Returns:
        SubmissionResultV2 conforming to Screen 2 contract
    """
    # Fetch problem details
    problem = await get_problem_by_id(connection, submission.problem_id)
    if not problem:
        raise ValueError(f"Problem {submission.problem_id} not found")

    # Fetch artifacts for evidence items
    artifacts = await get_submission_artifacts(connection, submission.id)

    # Build v2 components
    phase_scores = _generate_phase_scores(grading_report)
    evidence = _generate_evidence_items(artifacts)
    rubric_items = _generate_rubric_items(grading_report, problem.rubric_definition)
    radar = _generate_radar_dimensions(grading_report)
    strengths, weaknesses = _generate_strengths_weaknesses(grading_report)
    next_attempt_plan = _generate_next_attempt_plan(grading_report)
    follow_up_questions = _generate_follow_up_questions()
    reference_outline = _generate_reference_outline()

    # Build problem metadata
    problem_metadata = ProblemMetadata(
        id=problem.id,
        name=problem.title,  # Map title → name
        difficulty=problem.difficulty,
    )

    # Build phase_times dict (convert from submission.phase_times)
    phase_times = {phase: seconds for phase, seconds in submission.phase_times.items()}

    # Determine completed_at (if status is complete)
    completed_at = None
    if submission.status.value == "complete":
        # Use updated_at as proxy for completion time
        completed_at = submission.updated_at

    # Generate summary from phase observations (take first non-empty observation)
    summary = ""
    if grading_report.phase_observations:
        for phase, observation in grading_report.phase_observations.items():
            if observation:
                summary = observation
                break
    if not summary:
        summary = f"Overall performance: {grading_report.verdict.value}. Score: {grading_report.overall_score:.1f}/10"

    # Build the final v2 result
    return SubmissionResultV2(
        result_version=2,
        submission_id=submission.id,
        problem=problem_metadata,
        phase_times=phase_times,
        created_at=submission.created_at,
        completed_at=completed_at,
        phase_scores=phase_scores,
        evidence=evidence,
        rubric=rubric_items,
        radar=radar,
        overall_score=grading_report.overall_score,
        verdict=grading_report.verdict.value,
        summary=summary,
        strengths=strengths,
        weaknesses=weaknesses,
        highlights=[],  # v1 doesn't have highlights
        next_attempt_plan=next_attempt_plan,
        follow_up_questions=follow_up_questions,
        reference_outline=reference_outline,
    )


__all__ = ["build_submission_result_v2"]
