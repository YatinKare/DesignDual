#!/usr/bin/env python3
"""Test FinalAssemblerV2 integration into GradingPipelineV2."""

import sys
from pathlib import Path

# Add backend/app to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.agents import (
    create_final_assembler_v2,
    create_grading_pipeline_v2,
)


def test_final_assembler_instantiation():
    """Test that FinalAssemblerV2 can be instantiated."""
    agent = create_final_assembler_v2()
    assert agent is not None
    assert agent.name == "FinalAssemblerV2"
    assert agent.output_key == "final_report_v2"
    print("✅ FinalAssemblerV2 instantiation test passed")


def test_grading_pipeline_v2_structure():
    """Test that GradingPipelineV2 has correct structure with FinalAssemblerV2."""
    pipeline = create_grading_pipeline_v2()

    # Verify it's a SequentialAgent
    assert pipeline.name == "GradingPipelineV2"

    # Verify it has exactly 4 sub-agents now:
    # 1. ParallelAgent (PhaseEvaluationPanel)
    # 2. RubricRadarAgent
    # 3. PlanOutlineAgent
    # 4. FinalAssemblerV2
    assert len(pipeline.sub_agents) == 4, f"Expected 4 sub-agents, got {len(pipeline.sub_agents)}"

    # Verify first sub-agent is the parallel phase panel
    phase_panel = pipeline.sub_agents[0]
    assert phase_panel.name == "PhaseEvaluationPanel"
    assert len(phase_panel.sub_agents) == 4  # 4 phase agents

    # Verify phase agents have correct output_keys
    phase_output_keys = [agent.output_key for agent in phase_panel.sub_agents]
    expected_phase_keys = ["phase:clarify", "phase:estimate", "phase:design", "phase:explain"]
    assert phase_output_keys == expected_phase_keys, f"Phase keys: {phase_output_keys}"

    # Verify synthesis agents (LlmAgent has output_key)
    rubric_radar_agent = pipeline.sub_agents[1]
    assert rubric_radar_agent.name == "rubric_radar_agent"
    assert hasattr(rubric_radar_agent, 'output_key')
    assert rubric_radar_agent.output_key == "rubric_radar"

    plan_outline_agent = pipeline.sub_agents[2]
    assert plan_outline_agent.name == "PlanOutlineAgent"
    assert hasattr(plan_outline_agent, 'output_key')
    assert plan_outline_agent.output_key == "plan_outline"

    final_assembler = pipeline.sub_agents[3]
    assert final_assembler.name == "FinalAssemblerV2"
    assert hasattr(final_assembler, 'output_key')
    assert final_assembler.output_key == "final_report_v2"

    print("✅ GradingPipelineV2 structure test passed")
    print(f"   - Pipeline has 4 sub-agents (PhasePanel + 3 synthesis agents)")
    print(f"   - PhasePanel has 4 phase agents with correct output_keys")
    print(f"   - RubricRadarAgent: output_key='rubric_radar'")
    print(f"   - PlanOutlineAgent: output_key='plan_outline'")
    print(f"   - FinalAssemblerV2: output_key='final_report_v2' ✅ NEW")


def test_pipeline_output_keys():
    """Test that all agents have correct output_keys."""
    pipeline = create_grading_pipeline_v2()

    # Expected output_keys in session.state after pipeline runs
    expected_outputs = {
        "phase:clarify",
        "phase:estimate",
        "phase:design",
        "phase:explain",
        "rubric_radar",
        "plan_outline",
        "final_report_v2",
    }

    # Collect all output_keys from the pipeline
    actual_outputs = set()

    # Phase panel outputs
    phase_panel = pipeline.sub_agents[0]
    for agent in phase_panel.sub_agents:
        actual_outputs.add(agent.output_key)

    # Synthesis agent outputs
    for agent in pipeline.sub_agents[1:]:
        actual_outputs.add(agent.output_key)

    assert actual_outputs == expected_outputs, f"Output keys mismatch: {actual_outputs}"
    print("✅ Pipeline output_keys test passed")
    print(f"   - All 7 expected output_keys present: {sorted(expected_outputs)}")


if __name__ == "__main__":
    print("Running FinalAssemblerV2 integration tests...\n")
    test_final_assembler_instantiation()
    print()
    test_grading_pipeline_v2_structure()
    print()
    test_pipeline_output_keys()
    print("\n✅ All tests passed!")
