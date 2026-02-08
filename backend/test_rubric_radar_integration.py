"""
Validation test for RubricRadarAgent integration into GradingPipelineV2.

This test verifies:
1. RubricRadarAgent can be instantiated
2. GradingPipelineV2 includes RubricRadarAgent in the correct position
3. Pipeline structure is correct (phase agents → rubric/radar → future synthesis)
"""

from app.agents import create_grading_pipeline_v2, create_rubric_radar_agent


def test_rubric_radar_agent_instantiation():
    """Test that RubricRadarAgent can be instantiated."""
    agent = create_rubric_radar_agent()
    assert agent is not None
    assert agent.name == "rubric_radar_agent"
    assert agent.output_key == "rubric_radar"
    print("✅ RubricRadarAgent instantiation successful")


def test_pipeline_v2_structure():
    """Test that GradingPipelineV2 has correct structure with RubricRadarAgent."""
    pipeline = create_grading_pipeline_v2()

    # Check pipeline basics
    assert pipeline is not None
    assert pipeline.name == "GradingPipelineV2"

    # Check sub_agents count
    # Should have:
    # 1. ParallelAgent (PhaseEvaluationPanel)
    # 2. RubricRadarAgent
    # (Future: PlanOutlineAgent, FinalAssemblerV2)
    assert len(pipeline.sub_agents) == 2, f"Expected 2 sub-agents, got {len(pipeline.sub_agents)}"

    # Check first sub-agent is ParallelAgent
    phase_panel = pipeline.sub_agents[0]
    assert phase_panel.name == "PhaseEvaluationPanel"
    assert len(phase_panel.sub_agents) == 4, "PhaseEvaluationPanel should have 4 phase agents"

    # Check second sub-agent is RubricRadarAgent
    rubric_radar = pipeline.sub_agents[1]
    assert rubric_radar.name == "rubric_radar_agent"
    assert rubric_radar.output_key == "rubric_radar"

    print("✅ GradingPipelineV2 structure validated")
    print(f"   - ParallelAgent: {phase_panel.name} with {len(phase_panel.sub_agents)} phase agents")
    print(f"   - RubricRadarAgent: {rubric_radar.name} (output_key: {rubric_radar.output_key})")
    print(f"   - Total sub-agents in pipeline: {len(pipeline.sub_agents)}")


def test_phase_agents_output_keys():
    """Verify that phase agents have correct output_key pattern."""
    pipeline = create_grading_pipeline_v2()
    phase_panel = pipeline.sub_agents[0]

    expected_output_keys = ["phase:clarify", "phase:estimate", "phase:design", "phase:explain"]
    actual_output_keys = [agent.output_key for agent in phase_panel.sub_agents]

    assert actual_output_keys == expected_output_keys, \
        f"Phase agents output_keys mismatch. Expected: {expected_output_keys}, Got: {actual_output_keys}"

    print("✅ Phase agents output_keys validated")
    print(f"   Output keys: {actual_output_keys}")


if __name__ == "__main__":
    print("=" * 70)
    print("Testing RubricRadarAgent Integration (Task 7.3)")
    print("=" * 70)
    print()

    try:
        test_rubric_radar_agent_instantiation()
        print()
        test_pipeline_v2_structure()
        print()
        test_phase_agents_output_keys()
        print()
        print("=" * 70)
        print("✅ ALL TESTS PASSED - Task 7.3 Complete")
        print("=" * 70)
    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 70)
        exit(1)
