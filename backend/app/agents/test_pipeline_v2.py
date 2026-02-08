"""Test script for ADK agent pipeline v2.

This script tests the v2 grading pipeline (phase-based agents)
using mock submission data and text message passing pattern.

The key difference from the incorrectly working v2 test is that we:
1. Format submission data as a text message (like v1 does)
2. Pass this message to the pipeline via new_message parameter
3. Extract results from session state after pipeline completes

Usage:
    uv run python -m app.agents.test_pipeline_v2
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path

# Load .env file before importing ADK (at project root, not backend/)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agents import create_grading_pipeline_v2

# Mock problem for testing
MOCK_PROBLEM = {
    "id": "url-shortener",
    "title": "Design a URL Shortener",
    "name": "Design a URL Shortener",  # Alias for v2 compatibility
    "prompt": """Design a URL shortening service like bit.ly or TinyURL.

Requirements:
- Users can submit a long URL and get a shortened version
- When users access the short URL, redirect to original
- Track click analytics (optional)
- Handle high traffic (100M URLs, 10B redirects/month)

Constraints:
- Short URLs should be as short as possible
- Consider read-heavy traffic patterns
- Think about URL expiration policies
""",
    "difficulty": "medium",
    "focus_tags": ["system-design", "scalability", "databases"],
    "rubric_definition": [
        {
            "label": "Requirements Clarity",
            "description": "Ability to scope the problem and identify key requirements",
            "phase_weights": {"clarify": 0.7, "estimate": 0.3}
        },
        {
            "label": "Capacity Estimation",
            "description": "Accurate back-of-envelope calculations with stated assumptions",
            "phase_weights": {"estimate": 0.8, "design": 0.2}
        },
        {
            "label": "System Design",
            "description": "Clear architecture with appropriate component selection",
            "phase_weights": {"design": 0.8, "explain": 0.2}
        },
        {
            "label": "Scalability Plan",
            "description": "Concrete plans for handling scale and bottlenecks",
            "phase_weights": {"design": 0.5, "explain": 0.5}
        },
        {
            "label": "Tradeoff Analysis",
            "description": "Clear reasoning about technology choices and their tradeoffs",
            "phase_weights": {"explain": 0.9, "design": 0.1}
        },
    ],
}

# Mock transcripts for testing (simulating what the candidate said)
MOCK_TRANSCRIPTS = {
    "clarify": """
    [00:12] So for this URL shortener, let me first understand the requirements.
    [00:25] We need to support shortening long URLs to short ones.
    [00:38] For scale, I'm thinking about 100 million URLs stored, maybe 10 billion redirects per month.
    [00:52] That's about 4000 redirects per second on average.
    [01:05] The read to write ratio is probably 100:1 since redirects happen way more than creating new URLs.
    [01:18] For the MVP, I'll focus on basic shortening and redirecting.
    [01:28] Analytics can be a Phase 2 feature.
    """,
    "estimate": """
    [02:15] Let me do some back-of-envelope calculations.
    [02:28] For 100 million URLs, if each URL is about 500 bytes with metadata,
    [02:42] that's 50 GB of storage - very manageable.
    [02:55] For 4000 redirects per second, we need a read-heavy database.
    [03:08] If we want 6 character short codes with base62, that's 56 billion combinations.
    [03:22] We could use a key-value store like Redis for hot URLs.
    [03:35] I estimate we need maybe 3-5 application servers behind a load balancer.
    """,
    "design": """
    [04:15] Here's my high-level architecture.
    [04:25] At the top, we have a load balancer distributing traffic.
    [04:38] Behind that, I have stateless API servers handling both read and write requests.
    [04:52] For the database layer, I'm using a primary SQL database like PostgreSQL for durability.
    [05:05] In front of that, a Redis cache layer for frequently accessed URLs.
    [05:18] For short code generation, I'll use a counter-based approach with base62 encoding.
    [05:32] Write path: client -> load balancer -> API server -> generate short code -> write to DB -> cache.
    [05:48] Read path: client -> load balancer -> API server -> check cache -> if miss, check DB -> redirect.
    [06:02] I'm also adding a CDN layer for the absolute hottest URLs.
    """,
    "explain": """
    [07:15] For the tradeoffs, I chose SQL over NoSQL because we need strong consistency for URL mappings.
    [07:32] A user should never get a wrong redirect - that would be terrible UX.
    [07:45] Redis as cache is a classic choice for read-heavy workloads.
    [07:58] For the counter-based approach versus random IDs, counters give us predictable performance
    [08:12] and guaranteed uniqueness without collision checks.
    [08:22] However, they're sequential which could be a security concern.
    [08:35] If I had more time, I'd add rate limiting to prevent abuse,
    [08:48] implement the analytics feature with an async message queue,
    [09:02] and add geographic distribution for lower latency globally.
    [09:15] One weakness of my design is that the counter is a single point of failure -
    [09:28] I'd need to think about distributed counters for true high availability.
    """,
}

# Mock snapshot URLs (simulating storage artifacts)
MOCK_SNAPSHOT_URLS = {
    "clarify": "/uploads/test-submission/canvas_clarify.png",
    "estimate": "/uploads/test-submission/canvas_estimate.png",
    "design": "/uploads/test-submission/canvas_design.png",
    "explain": "/uploads/test-submission/canvas_explain.png",
}

# Mock phase times
MOCK_PHASE_TIMES = {
    "clarify": 90,   # 1.5 minutes
    "estimate": 120, # 2 minutes
    "design": 180,   # 3 minutes
    "explain": 150,  # 2.5 minutes
}


def format_v2_agent_input(problem: dict, phase_artifacts: dict, phase_times: dict) -> str:
    """Format submission data as agent input message for v2 pipeline.
    
    This follows the v1 pattern of passing data as a formatted text message,
    which is the proven way to get ADK agents to process the data.
    """
    sections = [
        "# System Design Interview Submission",
        "",
        "## Problem",
        f"**Title**: {problem['title']}",
        "",
        problem["prompt"],
        "",
        "---",
        "",
        "## Phase Artifacts and Transcripts",
        "",
    ]
    
    for phase in ["clarify", "estimate", "design", "explain"]:
        artifact = phase_artifacts.get(phase, {})
        time_sec = phase_times.get(phase, 0)
        
        sections.append(f"### Phase: {phase.upper()}")
        sections.append(f"**Time spent**: {time_sec} seconds")
        sections.append(f"**Canvas snapshot**: {artifact.get('snapshot_url', 'N/A')}")
        sections.append("")
        sections.append("**Transcript**:")
        sections.append("```")
        
        # Format transcripts with timestamps
        transcripts = artifact.get("transcripts", [])
        if isinstance(transcripts, list) and transcripts:
            for t in transcripts:
                ts = t.get("timestamp_sec", 0)
                text = t.get("text", "")
                sections.append(f"[{ts:.1f}s] {text}")
        elif isinstance(transcripts, str):
            sections.append(transcripts)
        else:
            sections.append("(No transcript available)")
        
        sections.append("```")
        sections.append("")
        sections.append("---")
        sections.append("")
    
    # Add rubric definition for synthesis agents
    sections.append("## Rubric Definition")
    sections.append("")
    for item in problem.get("rubric_definition", []):
        sections.append(f"- **{item['label']}**: {item['description']}")
        weights = item.get("phase_weights", {})
        weight_str = ", ".join([f"{k}={v}" for k, v in weights.items()])
        sections.append(f"  - Phase weights: {weight_str}")
    sections.append("")
    
    return "\n".join(sections)


def build_phase_artifacts() -> dict:
    """Build phase artifacts dict from mock data."""
    artifacts = {}
    for phase in ["clarify", "estimate", "design", "explain"]:
        # Parse transcript text into timestamped segments
        transcript_text = MOCK_TRANSCRIPTS[phase]
        transcripts = []
        
        # Extract timestamps from [MM:SS] format
        timestamp_pattern = re.compile(r'\[(\d+):(\d+)\](.+?)(?=\[|\Z)', re.DOTALL)
        matches = timestamp_pattern.findall(transcript_text)
        
        for mins, secs, text in matches:
            timestamp_sec = int(mins) * 60 + int(secs)
            transcripts.append({
                "timestamp_sec": float(timestamp_sec),
                "text": text.strip()
            })
        
        artifacts[phase] = {
            "snapshot_url": MOCK_SNAPSHOT_URLS[phase],
            "transcripts": transcripts
        }
    
    return artifacts


def extract_json_text(result_text: str) -> str | None:
    """Extract JSON payload from an LLM response that may include markdown fences."""
    fenced_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        result_text,
        flags=re.DOTALL,
    )
    if fenced_match:
        return fenced_match.group(1)

    json_start = result_text.find("{")
    json_end = result_text.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        return result_text[json_start:json_end]
    return None


async def test_v2_pipeline():
    """Test the full v2 grading pipeline with mock submission data."""
    print("\n" + "=" * 70)
    print("TESTING V2 GRADING PIPELINE")
    print("=" * 70)
    
    # Build mock data
    phase_artifacts = build_phase_artifacts()
    
    # Format as text message (KEY DIFFERENCE FROM BROKEN V2 TEST)
    input_message = format_v2_agent_input(
        problem=MOCK_PROBLEM,
        phase_artifacts=phase_artifacts,
        phase_times=MOCK_PHASE_TIMES
    )
    
    print(f"\n📝 Input message length: {len(input_message)} characters")
    print("\n📋 First 500 chars of input:")
    print("-" * 40)
    print(input_message[:500] + "...")
    
    # Create the v2 pipeline
    pipeline = create_grading_pipeline_v2()
    
    print(f"\n🔧 Pipeline: {pipeline.name}")
    print(f"   Sub-agents: {len(pipeline.sub_agents)}")
    for i, agent in enumerate(pipeline.sub_agents):
        print(f"   {i+1}. {agent.name}")
    
    print("\n🚀 Running v2 pipeline (ParallelAgent → Synthesis Agents)...")
    print("   This may take 2-3 minutes as all agents run...")
    
    runner = InMemoryRunner(agent=pipeline, app_name="test-v2")
    user_id = "test-user-v2"
    
    # Create a new session with initial state
    session = await runner.session_service.create_session(
        app_name="test-v2",
        user_id=user_id,
        state={
            # V2 session state structure
            "submission_id": "test-v2-submission",
            "problem": MOCK_PROBLEM,
            "phase_times": MOCK_PHASE_TIMES,
            "phase_artifacts": phase_artifacts,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            # Output slots (will be populated by agents)
            "phase:clarify": None,
            "phase:estimate": None,
            "phase:design": None,
            "phase:explain": None,
            "rubric_radar": None,
            "plan_outline": None,
            "final_report_v2": None,
        }
    )
    
    print(f"   Session ID: {session.id}")
    
    # Create the user message (KEY: Pass data as message, not just session state)
    user_content = types.Content(
        role="user",
        parts=[types.Part(text=input_message)]
    )
    
    result_text = ""
    event_count = 0
    agent_outputs = {}
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=user_content,
    ):
        event_count += 1
        
        # Collect text from agent responses
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    result_text += part.text + "\n---\n"
        
        # Show progress
        if event_count % 10 == 0:
            print(f"   ... processed {event_count} events")
    
    print(f"\n✅ Pipeline complete! Processed {event_count} events.")
    
    # Retrieve updated session state
    updated_session = await runner.session_service.get_session(
        app_name="test-v2",
        user_id=user_id,
        session_id=session.id,
    )
    
    session_state = updated_session.state if updated_session else {}
    
    # Collect outputs
    output_keys = [
        "phase:clarify", "phase:estimate", "phase:design", "phase:explain",
        "rubric_radar", "plan_outline", "final_report_v2"
    ]
    
    print("\n📊 Session State Outputs:")
    print("-" * 40)
    
    for key in output_keys:
        value = session_state.get(key)
        if value is not None:
            # Try to parse as JSON if it's a string
            if isinstance(value, str):
                try:
                    json_text = extract_json_text(value)
                    if json_text:
                        value = json.loads(json_text)
                except json.JSONDecodeError:
                    pass
            
            agent_outputs[key] = value
            
            if isinstance(value, dict):
                print(f"   ✅ {key}:")
                if "score" in value:
                    print(f"      Score: {value.get('score')}")
                if "phase" in value:
                    print(f"      Phase: {value.get('phase')}")
                if "verdict" in value:
                    print(f"      Verdict: {value.get('verdict')}")
                if "overall_score" in value:
                    print(f"      Overall: {value.get('overall_score')}")
            else:
                preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                print(f"   ✅ {key}: {preview}")
        else:
            print(f"   ❌ {key}: null")
    
    # Analyze results
    print("\n" + "=" * 70)
    print("RESULTS ANALYSIS")
    print("=" * 70)
    
    phase_outputs = {k: v for k, v in agent_outputs.items() if k.startswith("phase:")}
    synthesis_outputs = {k: v for k, v in agent_outputs.items() if not k.startswith("phase:")}
    
    print(f"\n📈 Phase Agents Completed: {len([v for v in phase_outputs.values() if v])}/4")
    print(f"📈 Synthesis Agents Completed: {len([v for v in synthesis_outputs.values() if v])}/3")
    
    # Check for final report
    final_report = agent_outputs.get("final_report_v2")
    if final_report and isinstance(final_report, dict):
        print("\n🎯 Final Report V2 Summary:")
        print(f"   Overall Score: {final_report.get('overall_score', 'N/A')}")
        print(f"   Verdict: {final_report.get('verdict', 'N/A')}")
        if "phase_scores" in final_report:
            print(f"   Phase Scores: {len(final_report.get('phase_scores', []))}")
        if "evidence" in final_report:
            print(f"   Evidence: {len(final_report.get('evidence', []))}")
        if "rubric" in final_report:
            print(f"   Rubric Items: {len(final_report.get('rubric', []))}")
    
    # Prepare results for saving
    results = {
        "test_timestamp": datetime.now().isoformat(),
        "event_count": event_count,
        "session_state_keys": list(session_state.keys()) if session_state else [],
        "agent_outputs": agent_outputs,
        "raw_response_preview": result_text[:5000] if result_text else "No text output",
    }
    
    # Save results to temp folder
    output_path = Path(__file__).parent.parent.parent / "temp" / "pipeline_v2_test_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to JSON-serializable format
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif hasattr(obj, "__dict__"):
            return str(obj)
        return obj
    
    with open(output_path, "w") as f:
        json.dump(make_serializable(results), f, indent=2)
    
    print(f"\n💾 Results saved to: {output_path}")
    
    return results


async def main():
    """Run the v2 pipeline test."""
    print("\n" + "#" * 70)
    print("# ADK AGENT PIPELINE V2 TEST")
    print("#" * 70)
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: No API key found!")
        print("Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
        return
    
    print(f"\n✅ API key found (ends with ...{api_key[-4:]})")
    
    # Test v2 pipeline
    try:
        results = await test_v2_pipeline()
        
        print("\n" + "=" * 70)
        print("V2 PIPELINE TEST COMPLETE")
        print("=" * 70)
        
        # Final summary
        outputs = results.get("agent_outputs", {})
        successful = sum(1 for v in outputs.values() if v is not None)
        total = 7  # 4 phase + 3 synthesis
        
        if successful == total:
            print("\n🎉 SUCCESS! All 7 agent outputs captured!")
        elif successful > 0:
            print(f"\n⚠️  PARTIAL SUCCESS: {successful}/{total} agent outputs captured")
            print("   Check temp/pipeline_v2_test_results.json for details")
        else:
            print("\n❌ FAILURE: No agent outputs captured")
            print("   The agents may not be processing the input correctly")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "#" * 70)
    print("# TEST COMPLETE")
    print("#" * 70)


if __name__ == "__main__":
    asyncio.run(main())
