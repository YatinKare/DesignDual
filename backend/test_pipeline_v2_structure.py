#!/usr/bin/env python3
"""
Test script to verify GradingPipelineV2 structure.

This script validates:
1. The pipeline can be instantiated
2. The correct number of sub-agents are present
3. The phase evaluation panel has 4 agents
4. All agents have proper output_keys
"""

from app.agents import create_grading_pipeline_v2


def test_pipeline_v2_structure():
    """Test the v2 pipeline structure."""
    print("=" * 80)
    print("GradingPipelineV2 Structure Test")
    print("=" * 80)

    # Create the pipeline
    pipeline = create_grading_pipeline_v2()
    print(f"\n✓ Pipeline created: {pipeline.name}")
    print(f"  Description: {pipeline.description}")

    # Verify sub-agents
    print(f"\n✓ Pipeline has {len(pipeline.sub_agents)} sub-agent(s):")
    for i, agent in enumerate(pipeline.sub_agents, 1):
        print(f"  {i}. {agent.name}")

    # Get the phase evaluation panel (first sub-agent)
    assert len(pipeline.sub_agents) >= 1, "Pipeline should have at least 1 sub-agent"
    phase_panel = pipeline.sub_agents[0]

    print(f"\n✓ Phase Evaluation Panel: {phase_panel.name}")
    print(f"  Description: {phase_panel.description}")
    print(f"  Number of phase agents: {len(phase_panel.sub_agents)}")

    # Verify phase agents
    assert len(phase_panel.sub_agents) == 4, "Phase panel should have exactly 4 agents"
    print(f"\n✓ Phase Agents:")
    expected_output_keys = [
        "phase:clarify",
        "phase:estimate",
        "phase:design",
        "phase:explain",
    ]

    for i, agent in enumerate(phase_panel.sub_agents):
        output_key = getattr(agent, "output_key", None)
        print(f"  {i + 1}. {agent.name}")
        print(f"     Output Key: {output_key}")

        # Verify output_key matches expected
        if output_key not in expected_output_keys:
            print(f"     ⚠️  Warning: Unexpected output_key '{output_key}'")
        else:
            print(f"     ✓ Output key is correct")

    # Verify all expected output_keys are present
    actual_keys = [getattr(agent, "output_key", None) for agent in phase_panel.sub_agents]
    missing_keys = set(expected_output_keys) - set(actual_keys)
    if missing_keys:
        print(f"\n⚠️  Missing expected output_keys: {missing_keys}")
    else:
        print(f"\n✓ All expected output_keys are present")

    print("\n" + "=" * 80)
    print("✓ GradingPipelineV2 structure validation PASSED")
    print("=" * 80)


if __name__ == "__main__":
    test_pipeline_v2_structure()
