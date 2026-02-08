"""ADK agents for system design interview grading."""

from .base import DEFAULT_MODEL, GRADING_SCALE, AgentResult, get_model_name
from .design_agent import design_agent
from .orchestrator import grading_pipeline, parallel_evaluation_agent
from .orchestrator_v2 import create_grading_pipeline_v2
from .scale_agent import scale_agent
from .scoping_agent import scoping_agent
from .synthesis_agent import synthesis_agent
from .tradeoff_agent import tradeoff_agent

# Phase agents (v2)
from .phase_agents import (
    create_clarify_phase_agent,
    create_design_phase_agent,
    create_estimate_phase_agent,
    create_explain_phase_agent,
)

__all__ = [
    # Pipeline and orchestrators (v1)
    "grading_pipeline",
    "parallel_evaluation_agent",
    # Pipeline and orchestrators (v2)
    "create_grading_pipeline_v2",
    # Individual agents (v1)
    "scoping_agent",
    "design_agent",
    "scale_agent",
    "tradeoff_agent",
    "synthesis_agent",
    # Phase agents (v2)
    "create_clarify_phase_agent",
    "create_estimate_phase_agent",
    "create_design_phase_agent",
    "create_explain_phase_agent",
    # Utilities
    "AgentResult",
    "DEFAULT_MODEL",
    "GRADING_SCALE",
    "get_model_name",
]
