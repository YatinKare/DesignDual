"""Test script for ADK agent pipeline.

This script tests individual agents and the full grading pipeline
using mock submission data.

Usage:
    uv run python -m app.agents.test_pipeline
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
from pathlib import Path

# Load .env file before importing ADK (at project root, not backend/)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agents import (
    grading_pipeline,
    scoping_agent,
    design_agent,
    scale_agent,
    tradeoff_agent,
    synthesis_agent,
)

# Base path for test assets
STORAGE_BASE = Path(__file__).parent.parent.parent / "storage" / "uploads"
TEST_SUBMISSION_ID = "36081f88-d0e0-4b2d-8071-6da870fe60bf"

# Mock problem for testing
MOCK_PROBLEM = {
    "id": "url-shortener",
    "title": "Design a URL Shortener",
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
}

# Mock transcripts for testing (simulating what the candidate said)
MOCK_TRANSCRIPTS = {
    "clarify": """
    So for this URL shortener, let me first understand the requirements.
    We need to support shortening long URLs to short ones.
    For scale, I'm thinking about 100 million URLs stored, maybe 10 billion redirects per month.
    That's about 4000 redirects per second on average.
    The read to write ratio is probably 100:1 since redirects happen way more than creating new URLs.
    For the MVP, I'll focus on basic shortening and redirecting.
    Analytics can be a Phase 2 feature.
    """,
    "estimate": """
    Let me do some back-of-envelope calculations.
    For 100 million URLs, if each URL is about 500 bytes with metadata,
    that's 50 GB of storage - very manageable.
    For 4000 redirects per second, we need a read-heavy database.
    If we want 6 character short codes with base62, that's 56 billion combinations.
    We could use a key-value store like Redis for hot URLs.
    I estimate we need maybe 3-5 application servers behind a load balancer.
    """,
    "design": """
    Here's my high-level architecture.
    At the top, we have a load balancer distributing traffic.
    Behind that, I have stateless API servers handling both read and write requests.
    For the database layer, I'm using a primary SQL database like PostgreSQL for durability.
    In front of that, a Redis cache layer for frequently accessed URLs.
    For short code generation, I'll use a counter-based approach with base62 encoding.
    Write path: client -> load balancer -> API server -> generate short code -> write to DB -> cache.
    Read path: client -> load balancer -> API server -> check cache -> if miss, check DB -> redirect.
    I'm also adding a CDN layer for the absolute hottest URLs.
    """,
    "explain": """
    For the tradeoffs, I chose SQL over NoSQL because we need strong consistency for URL mappings.
    A user should never get a wrong redirect - that would be terrible UX.
    Redis as cache is a classic choice for read-heavy workloads.
    For the counter-based approach versus random IDs, counters give us predictable performance
    and guaranteed uniqueness without collision checks.
    However, they're sequential which could be a security concern.
    If I had more time, I'd add rate limiting to prevent abuse,
    implement the analytics feature with an async message queue,
    and add geographic distribution for lower latency globally.
    One weakness of my design is that the counter is a single point of failure -
    I'd need to think about distributed counters for true high availability.
    """,
}


def load_canvas_as_base64(phase: str) -> str:
    """Load a canvas PNG and convert to base64."""
    canvas_path = STORAGE_BASE / TEST_SUBMISSION_ID / f"canvas_{phase}.png"
    if canvas_path.exists():
        with open(canvas_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    # Return a tiny placeholder if no real image exists
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def build_submission_bundle() -> dict:
    """Build a mock submission bundle for testing."""
    return {
        "problem": MOCK_PROBLEM,
        "phases": {
            "clarify": {
                "canvas_base64": load_canvas_as_base64("clarify"),
                "transcript": MOCK_TRANSCRIPTS["clarify"],
            },
            "estimate": {
                "canvas_base64": load_canvas_as_base64("estimate"),
                "transcript": MOCK_TRANSCRIPTS["estimate"],
            },
            "design": {
                "canvas_base64": load_canvas_as_base64("design"),
                "transcript": MOCK_TRANSCRIPTS["design"],
            },
            "explain": {
                "canvas_base64": load_canvas_as_base64("explain"),
                "transcript": MOCK_TRANSCRIPTS["explain"],
            },
        },
    }


def format_agent_input(bundle: dict, phases: list[str]) -> str:
    """Format submission data as agent input message."""
    problem = bundle["problem"]
    
    sections = [
        f"# Problem: {problem['title']}",
        "",
        problem["prompt"],
        "",
        "---",
        "",
    ]
    
    for phase in phases:
        phase_data = bundle["phases"][phase]
        sections.append(f"## Phase: {phase.title()}")
        sections.append("")
        sections.append(f"### Transcript:")
        sections.append(phase_data["transcript"])
        sections.append("")
        sections.append(f"[Canvas image for {phase} phase attached]")
        sections.append("")
        sections.append("---")
        sections.append("")
    
    return "\n".join(sections)


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


async def test_single_agent(agent, input_text: str, agent_name: str) -> dict:
    """Test a single agent and return its output."""
    print(f"\n{'='*60}")
    print(f"Testing {agent_name}")
    print(f"{'='*60}")
    
    runner = InMemoryRunner(agent=agent, app_name="test")
    user_id = "test-user"
    
    # Create a new session using the runner's session service
    session = await runner.session_service.create_session(
        app_name="test",
        user_id=user_id,
    )
    
    # Create the user message
    user_content = types.Content(
        role="user",
        parts=[types.Part(text=input_text)]
    )
    
    result_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=user_content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    result_text += part.text
    
    print(f"\n{agent_name} Output (first 500 chars):")
    print("-" * 40)
    print(result_text[:500] + "..." if len(result_text) > 500 else result_text)
    
    # Try to parse as JSON
    try:
        json_text = extract_json_text(result_text)
        if json_text:
            result_json = json.loads(json_text)
            print(f"\n✅ {agent_name} returned valid JSON")
            return result_json
    except json.JSONDecodeError:
        print(f"\n⚠️ {agent_name} did not return valid JSON")
    
    return {"raw_output": result_text}


async def test_individual_agents():
    """Test each specialist agent individually."""
    print("\n" + "=" * 70)
    print("TESTING INDIVIDUAL AGENTS")
    print("=" * 70)
    
    bundle = build_submission_bundle()
    
    # Test ScopingAgent (phases 1-2)
    scoping_input = format_agent_input(bundle, ["clarify", "estimate"])
    scoping_result = await test_single_agent(
        scoping_agent, scoping_input, "ScopingAgent"
    )
    
    # Test DesignAgent (phase 3)
    design_input = format_agent_input(bundle, ["design"])
    design_result = await test_single_agent(
        design_agent, design_input, "DesignAgent"
    )
    
    # Test ScaleAgent (all phases)
    scale_input = format_agent_input(bundle, ["clarify", "estimate", "design", "explain"])
    scale_result = await test_single_agent(
        scale_agent, scale_input, "ScaleAgent"
    )
    
    # Test TradeoffAgent (phases 3-4)
    tradeoff_input = format_agent_input(bundle, ["design", "explain"])
    tradeoff_result = await test_single_agent(
        tradeoff_agent, tradeoff_input, "TradeoffAgent"
    )
    
    return {
        "scoping_result": scoping_result,
        "design_result": design_result,
        "scale_result": scale_result,
        "tradeoff_result": tradeoff_result,
    }


async def test_full_pipeline():
    """Test the full grading pipeline with orchestration."""
    print("\n" + "=" * 70)
    print("TESTING FULL GRADING PIPELINE")
    print("=" * 70)
    
    bundle = build_submission_bundle()
    full_input = format_agent_input(
        bundle, ["clarify", "estimate", "design", "explain"]
    )
    
    print("\nRunning full pipeline (ParallelAgent → SynthesisAgent)...")
    print("This may take a minute as all agents run...")
    
    runner = InMemoryRunner(agent=grading_pipeline, app_name="test")
    user_id = "test-user"
    
    # Create a new session using the runner's session service
    session = await runner.session_service.create_session(
        app_name="test",
        user_id=user_id,
    )
    
    user_content = types.Content(
        role="user",
        parts=[types.Part(text=full_input)]
    )
    
    result_text = ""
    event_count = 0
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=user_content,
    ):
        event_count += 1
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    result_text += part.text
        
        # Show progress
        if event_count % 5 == 0:
            print(f"  ... processed {event_count} events")
    
    print(f"\nPipeline complete! Processed {event_count} events.")
    print("\nFinal Output (first 1000 chars):")
    print("-" * 40)
    print(result_text[:1000] + "..." if len(result_text) > 1000 else result_text)
    
    # Try to parse final report
    try:
        json_text = extract_json_text(result_text)
        if json_text:
            final_report = json.loads(json_text)
            print("\n✅ Pipeline returned valid JSON report")
            if "overall_score" in final_report:
                print(f"   Overall Score: {final_report['overall_score']}")
            if "verdict" in final_report:
                print(f"   Verdict: {final_report['verdict']}")
            return final_report
    except json.JSONDecodeError:
        print("\n⚠️ Pipeline did not return valid JSON")
    
    return {"raw_output": result_text}


async def main():
    """Run all agent tests."""
    print("\n" + "#" * 70)
    print("# ADK AGENT PIPELINE TEST")
    print("#" * 70)
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: No API key found!")
        print("Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
        return
    
    print(f"\n✅ API key found (ends with ...{api_key[-4:]})")
    
    # Test individual agents first
    try:
        individual_results = await test_individual_agents()
        print("\n\n" + "=" * 70)
        print("INDIVIDUAL AGENT TESTS COMPLETE")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Individual agent tests failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test full pipeline
    try:
        pipeline_result = await test_full_pipeline()
        print("\n\n" + "=" * 70)
        print("FULL PIPELINE TEST COMPLETE")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Save results to temp folder for later testing
    results = {
        "individual_results": individual_results,
        "pipeline_result": pipeline_result,
    }
    
    output_path = Path(__file__).parent.parent.parent / "temp" / "agent_test_results.json"
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
    
    print(f"\n✅ Results saved to: {output_path}")
    print("\n" + "#" * 70)
    print("# ALL TESTS COMPLETE")
    print("#" * 70)


if __name__ == "__main__":
    asyncio.run(main())
