"""
Test suite for PlanOutlineAgent integration into GradingPipelineV2.

This test verifies:
1. PlanOutlineAgent can be instantiated
2. GradingPipelineV2 has the correct structure with 3 sub-agents
3. All output_keys are correctly configured
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.agents import create_grading_pipeline_v2, create_plan_outline_agent


def test_plan_outline_agent_creation():
    """Test 1: PlanOutlineAgent instantiation."""
    print("Test 1: PlanOutlineAgent instantiation")

    agent = create_plan_outline_agent()

    assert agent.name == "PlanOutlineAgent", f"Expected name 'PlanOutlineAgent', got '{agent.name}'"
    assert agent.output_key == "plan_outline", f"Expected output_key 'plan_outline', got '{agent.output_key}'"

    print("  ✅ PlanOutlineAgent created successfully")
    print(f"     Name: {agent.name}")
    print(f"     Output key: {agent.output_key}")
    print()


def test_grading_pipeline_v2_structure():
    """Test 2: GradingPipelineV2 has correct structure."""
    print("Test 2: GradingPipelineV2 structure validation")

    pipeline = create_grading_pipeline_v2()

    assert pipeline.name == "GradingPipelineV2", f"Expected pipeline name 'GradingPipelineV2', got '{pipeline.name}'"

    # Should have 3 sub-agents:
    # 1. ParallelAgent (PhaseEvaluationPanel)
    # 2. RubricRadarAgent
    # 3. PlanOutlineAgent
    sub_agents = pipeline.sub_agents
    assert len(sub_agents) == 3, f"Expected 3 sub-agents, got {len(sub_agents)}"

    print("  ✅ GradingPipelineV2 has correct structure")
    print(f"     Pipeline name: {pipeline.name}")
    print(f"     Number of sub-agents: {len(sub_agents)}")
    print()

    # Validate sub-agents
    print("  Sub-agents:")
    for i, agent in enumerate(sub_agents, 1):
        print(f"    {i}. {agent.name} (output_key: {getattr(agent, 'output_key', 'N/A')})")
    print()


def test_phase_agents_output_keys():
    """Test 3: Phase agents within ParallelAgent have correct output_keys."""
    print("Test 3: Phase agents output_keys validation")

    pipeline = create_grading_pipeline_v2()
    phase_panel = pipeline.sub_agents[0]  # First sub-agent is ParallelAgent

    assert phase_panel.name == "PhaseEvaluationPanel", f"Expected 'PhaseEvaluationPanel', got '{phase_panel.name}'"

    phase_agents = phase_panel.sub_agents
    assert len(phase_agents) == 4, f"Expected 4 phase agents, got {len(phase_agents)}"

    # Verify output_keys match expected pattern
    expected_keys = {"phase:clarify", "phase:estimate", "phase:design", "phase:explain"}
    actual_keys = {agent.output_key for agent in phase_agents}

    assert actual_keys == expected_keys, f"Output keys mismatch.\nExpected: {expected_keys}\nActual: {actual_keys}"

    print("  ✅ All 4 phase agents have correct output_keys")
    for agent in phase_agents:
        print(f"     - {agent.name}: {agent.output_key}")
    print()


def test_synthesis_agents_output_keys():
    """Test 4: Synthesis agents have correct output_keys."""
    print("Test 4: Synthesis agents output_keys validation")

    pipeline = create_grading_pipeline_v2()

    # Sub-agent 2: rubric_radar_agent
    rubric_radar = pipeline.sub_agents[1]
    assert rubric_radar.output_key == "rubric_radar", f"Expected output_key 'rubric_radar', got '{rubric_radar.output_key}'"

    # Sub-agent 3: PlanOutlineAgent
    plan_outline = pipeline.sub_agents[2]
    assert plan_outline.name == "PlanOutlineAgent", f"Expected 'PlanOutlineAgent', got '{plan_outline.name}'"
    assert plan_outline.output_key == "plan_outline", f"Expected output_key 'plan_outline', got '{plan_outline.output_key}'"

    print("  ✅ Both synthesis agents have correct output_keys")
    print(f"     - {rubric_radar.name}: {rubric_radar.output_key}")
    print(f"     - {plan_outline.name}: {plan_outline.output_key}")
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("PlanOutlineAgent Integration Tests")
    print("=" * 70)
    print()

    try:
        test_plan_outline_agent_creation()
        test_grading_pipeline_v2_structure()
        test_phase_agents_output_keys()
        test_synthesis_agents_output_keys()

        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("  - PlanOutlineAgent created successfully")
        print("  - GradingPipelineV2 has 3 sub-agents (1 ParallelAgent + 2 synthesis agents)")
        print("  - All output_keys correctly configured")
        print("  - Pipeline ready for task 7.5 (FinalAssemblerV2)")

    except AssertionError as e:
        print("=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        sys.exit(1)
