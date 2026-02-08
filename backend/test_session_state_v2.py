"""Validation test for v2 session state structure."""

import sys
from pathlib import Path

# Add backend/app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.grading import build_grading_session_state_v2


def test_session_state_v2_structure():
    """Verify v2 session state has correct structure."""

    # Mock submission bundle (v2 format)
    submission_bundle = {
        "submission_id": "test-uuid-123",
        "problem": {
            "id": "url-shortener",
            "title": "Design a URL Shortener",
            "rubric_definition": [
                {
                    "label": "Requirements Clarity",
                    "description": "Clear understanding of functional and non-functional requirements",
                    "phase_weights": {"clarify": 0.7, "estimate": 0.3}
                }
            ]
        },
        "phase_times": {
            "clarify": 300,
            "estimate": 400,
            "design": 600,
            "explain": 400
        },
        "phase_artifacts": {
            "clarify": {
                "snapshot_url": "/uploads/test-uuid-123/canvas_clarify.png",
                "transcripts": [
                    {"timestamp_sec": 10.5, "text": "Let me start by understanding the requirements..."},
                    {"timestamp_sec": 45.2, "text": "We need to handle about 10 million URLs per month"}
                ]
            },
            "estimate": {
                "snapshot_url": "/uploads/test-uuid-123/canvas_estimate.png",
                "transcripts": []
            },
            "design": {
                "snapshot_url": "/uploads/test-uuid-123/canvas_design.png",
                "transcripts": [
                    {"timestamp_sec": 20.0, "text": "I'll use a hash function for the short URLs"}
                ]
            },
            "explain": {
                "snapshot_url": "/uploads/test-uuid-123/canvas_explain.png",
                "transcripts": []
            }
        },
        "created_at": "2026-02-08T10:30:00",
        "completed_at": None
    }

    # Build v2 session state
    session_state = build_grading_session_state_v2(submission_bundle)

    # Validate input fields
    assert session_state["submission_id"] == "test-uuid-123", "submission_id mismatch"
    assert session_state["problem"]["id"] == "url-shortener", "problem.id mismatch"
    assert "rubric_definition" in session_state["problem"], "rubric_definition missing"
    assert session_state["phase_times"]["clarify"] == 300, "phase_times.clarify mismatch"
    assert "phase_artifacts" in session_state, "phase_artifacts missing"
    assert "clarify" in session_state["phase_artifacts"], "phase_artifacts.clarify missing"
    assert session_state["phase_artifacts"]["clarify"]["snapshot_url"] == "/uploads/test-uuid-123/canvas_clarify.png"
    assert len(session_state["phase_artifacts"]["clarify"]["transcripts"]) == 2, "transcript count mismatch"
    assert session_state["created_at"] == "2026-02-08T10:30:00", "created_at mismatch"
    assert session_state["completed_at"] is None, "completed_at should be None initially"

    # Validate v2 output slots (phase-based)
    assert "phase:clarify" in session_state, "phase:clarify output slot missing"
    assert "phase:estimate" in session_state, "phase:estimate output slot missing"
    assert "phase:design" in session_state, "phase:design output slot missing"
    assert "phase:explain" in session_state, "phase:explain output slot missing"
    assert session_state["phase:clarify"] is None, "phase:clarify should be None initially"
    assert session_state["phase:estimate"] is None, "phase:estimate should be None initially"
    assert session_state["phase:design"] is None, "phase:design should be None initially"
    assert session_state["phase:explain"] is None, "phase:explain should be None initially"

    # Validate synthesis output slots
    assert "rubric_radar" in session_state, "rubric_radar output slot missing"
    assert "plan_outline" in session_state, "plan_outline output slot missing"
    assert "final_report_v2" in session_state, "final_report_v2 output slot missing"
    assert session_state["rubric_radar"] is None, "rubric_radar should be None initially"
    assert session_state["plan_outline"] is None, "plan_outline should be None initially"
    assert session_state["final_report_v2"] is None, "final_report_v2 should be None initially"

    # Validate v1 output slots are NOT present
    assert "scoping_result" not in session_state, "v1 scoping_result should not be present"
    assert "design_result" not in session_state, "v1 design_result should not be present"
    assert "scale_result" not in session_state, "v1 scale_result should not be present"
    assert "tradeoff_result" not in session_state, "v1 tradeoff_result should not be present"
    assert "final_report" not in session_state, "v1 final_report should not be present"

    # Validate v1 phases array is NOT present
    assert "phases" not in session_state, "v1 phases array should not be present"

    print("✅ All v2 session state structure checks passed!")
    print(f"   - Input fields: submission_id, problem, phase_times, phase_artifacts, created_at, completed_at")
    print(f"   - Phase output slots: phase:clarify, phase:estimate, phase:design, phase:explain")
    print(f"   - Synthesis output slots: rubric_radar, plan_outline, final_report_v2")
    print(f"   - V1 fields correctly excluded: phases, scoping_result, design_result, scale_result, tradeoff_result, final_report")
    return True


if __name__ == "__main__":
    try:
        test_session_state_v2_structure()
        print("\n✅ TEST PASSED: V2 session state structure is correct")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
