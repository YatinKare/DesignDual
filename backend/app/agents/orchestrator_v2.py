"""
GradingPipelineV2 - Phase-based orchestration for v2 contract compliance.

This orchestrator creates a pipeline that:
1. Runs 4 phase agents in parallel (clarify, estimate, design, explain)
2. Sequential synthesis (future agents for rubric/radar/plan/assembler)

Architecture:
    SequentialAgent: GradingPipelineV2
    └── ParallelAgent: PhaseEvaluationPanel
        ├── ClarifyPhaseAgent  (output_key: "phase:clarify")
        ├── EstimatePhaseAgent (output_key: "phase:estimate")
        ├── DesignPhaseAgent   (output_key: "phase:design")
        └── ExplainPhaseAgent  (output_key: "phase:explain")
"""

from __future__ import annotations

from google.adk.agents import ParallelAgent, SequentialAgent

from .phase_agents import (
    create_clarify_phase_agent,
    create_design_phase_agent,
    create_estimate_phase_agent,
    create_explain_phase_agent,
)
from .rubric_radar_agent import create_rubric_radar_agent


def create_grading_pipeline_v2() -> SequentialAgent:
    """
    Creates the GradingPipelineV2 orchestrator.

    This is the main entry point for v2 grading that produces SubmissionResultV2 outputs.

    Returns:
        SequentialAgent: The full grading pipeline with phase agents running in parallel.

    Session State Structure (v2):
        Input (set by grading service):
            - problem: Problem metadata with rubric_definition
            - phase_artifacts: Dict mapping phase → {canvas_url, transcripts, snapshot_url}
            - phase_times: Dict mapping phase → seconds

        Output (written by agents):
            - phase:clarify: PhaseAgentOutput for clarify phase
            - phase:estimate: PhaseAgentOutput for estimate phase
            - phase:design: PhaseAgentOutput for design phase
            - phase:explain: PhaseAgentOutput for explain phase

        Future outputs (partially implemented):
            - rubric_radar: RubricRadarAgent output (rubric items, radar, verdict) - ✅ IMPLEMENTED
            - plan_outline: PlanOutlineAgent output (next_attempt_plan, follow_up_questions, reference)
            - final_report_v2: FinalAssemblerV2 output (complete SubmissionResultV2)
    """
    # Create the 4 phase agents
    clarify_agent = create_clarify_phase_agent()
    estimate_agent = create_estimate_phase_agent()
    design_agent = create_design_phase_agent()
    explain_agent = create_explain_phase_agent()

    # ParallelAgent: All 4 phase agents run concurrently
    # Each writes to its own output_key in session.state
    phase_evaluation_panel = ParallelAgent(
        name="PhaseEvaluationPanel",
        description="Runs all 4 phase evaluation agents in parallel",
        sub_agents=[
            clarify_agent,
            estimate_agent,
            design_agent,
            explain_agent,
        ],
    )

    # Create synthesis agents
    rubric_radar_agent = create_rubric_radar_agent()

    # SequentialAgent: Orchestrates the full v2 pipeline
    # Step 1: Run all 4 phase agents in parallel
    # Step 2: Compute rubric, radar, overall score, and verdict
    # Step 3 (future): Generate next_attempt_plan and follow_up_questions
    # Step 4 (future): Assemble final SubmissionResultV2
    grading_pipeline_v2 = SequentialAgent(
        name="GradingPipelineV2",
        description="Full v2 grading pipeline: phase agents → rubric/radar → plan/outline → final assembly",
        sub_agents=[
            phase_evaluation_panel,
            rubric_radar_agent,  # ✅ Task 7.3 complete
            # TODO (task 7.4): Add PlanOutlineAgent here
            # TODO (task 7.5): Add FinalAssemblerV2 here
        ],
    )

    return grading_pipeline_v2


__all__ = [
    "create_grading_pipeline_v2",
]
