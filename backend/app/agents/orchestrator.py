"""Orchestrator - Combines agents with SequentialAgent + ParallelAgent for pipeline."""

from __future__ import annotations

from google.adk.agents import ParallelAgent, SequentialAgent

from .design_agent import design_agent
from .scale_agent import scale_agent
from .scoping_agent import scoping_agent
from .synthesis_agent import synthesis_agent
from .tradeoff_agent import tradeoff_agent

# ParallelAgent runs all 4 specialist agents concurrently
# Each writes their output to their respective output_key in session state
parallel_evaluation_agent = ParallelAgent(
    name="ParallelEvaluationAgent",
    description="Runs all specialist evaluation agents in parallel",
    sub_agents=[
        scoping_agent,
        design_agent,
        scale_agent,
        tradeoff_agent,
    ],
)

# SequentialAgent orchestrates the full pipeline:
# 1. Run all specialists in parallel
# 2. Synthesis agent combines their outputs
grading_pipeline = SequentialAgent(
    name="GradingPipeline",
    description="Full grading pipeline: parallel evaluation followed by synthesis",
    sub_agents=[
        parallel_evaluation_agent,
        synthesis_agent,
    ],
)

__all__ = [
    "grading_pipeline",
    "parallel_evaluation_agent",
    "scoping_agent",
    "design_agent",
    "scale_agent",
    "tradeoff_agent",
    "synthesis_agent",
]
