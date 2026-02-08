#!/usr/bin/env python3
"""Test script for legacy status compatibility mapping."""

import sys
from pathlib import Path

# Add backend/app to path for imports
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.contract_v2 import StreamStatus
from app.services.status_compat import (
    LEGACY_TO_V2_MAP,
    V2_TO_LEGACY_MAP,
    legacy_status_to_v2,
    normalize_status_input,
    v2_status_to_legacy,
)


def test_legacy_to_v2_mapping():
    """Test legacy v1 status strings map correctly to v2 StreamStatus enum."""
    print("\n=== Testing legacy_status_to_v2() ===")

    test_cases = [
        ("scoping", StreamStatus.CLARIFY),
        ("design", StreamStatus.DESIGN),
        ("scale", StreamStatus.ESTIMATE),
        ("tradeoff", StreamStatus.EXPLAIN),
        ("synthesizing", StreamStatus.SYNTHESIZING),
        ("complete", StreamStatus.COMPLETE),
        ("failed", StreamStatus.FAILED),
        ("invalid_status", None),
    ]

    all_passed = True
    for legacy_status, expected in test_cases:
        result = legacy_status_to_v2(legacy_status)
        passed = result == expected
        all_passed = all_passed and passed
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} '{legacy_status}' → {result} (expected: {expected})")

    return all_passed


def test_v2_to_legacy_mapping():
    """Test v2 StreamStatus enum values map correctly to legacy v1 strings."""
    print("\n=== Testing v2_status_to_legacy() ===")

    test_cases = [
        (StreamStatus.CLARIFY, "scoping"),
        (StreamStatus.DESIGN, "design"),
        (StreamStatus.ESTIMATE, "scale"),
        (StreamStatus.EXPLAIN, "tradeoff"),
        (StreamStatus.SYNTHESIZING, "synthesizing"),
        (StreamStatus.COMPLETE, "complete"),
        (StreamStatus.FAILED, "failed"),
        (StreamStatus.QUEUED, None),  # New v2-only status
        (StreamStatus.PROCESSING, None),  # New v2-only status
    ]

    all_passed = True
    for v2_status, expected in test_cases:
        result = v2_status_to_legacy(v2_status)
        passed = result == expected
        all_passed = all_passed and passed
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} {v2_status} → '{result}' (expected: '{expected}')")

    return all_passed


def test_normalize_status_input():
    """Test normalize_status_input() handles all formats correctly."""
    print("\n=== Testing normalize_status_input() ===")

    test_cases = [
        # Legacy v1 strings
        ("scoping", StreamStatus.CLARIFY),
        ("scale", StreamStatus.ESTIMATE),
        ("tradeoff", StreamStatus.EXPLAIN),
        # New v2 strings
        ("clarify", StreamStatus.CLARIFY),
        ("estimate", StreamStatus.ESTIMATE),
        ("explain", StreamStatus.EXPLAIN),
        ("queued", StreamStatus.QUEUED),
        ("processing", StreamStatus.PROCESSING),
        # Already v2 enum
        (StreamStatus.CLARIFY, StreamStatus.CLARIFY),
        (StreamStatus.COMPLETE, StreamStatus.COMPLETE),
    ]

    all_passed = True
    for input_status, expected in test_cases:
        try:
            result = normalize_status_input(input_status)
            passed = result == expected
            all_passed = all_passed and passed
            status_icon = "✅" if passed else "❌"
            input_repr = (
                f"StreamStatus.{input_status.name}"
                if isinstance(input_status, StreamStatus)
                else f"'{input_status}'"
            )
            print(f"{status_icon} {input_repr} → {result} (expected: {expected})")
        except ValueError as e:
            print(f"❌ {input_status} → Error: {e}")
            all_passed = False

    # Test invalid input
    print("\n--- Testing invalid inputs (should raise ValueError) ---")
    invalid_inputs = ["invalid", "wrong_status", ""]
    for invalid_input in invalid_inputs:
        try:
            result = normalize_status_input(invalid_input)
            print(f"❌ '{invalid_input}' → {result} (should have raised ValueError)")
            all_passed = False
        except ValueError as e:
            print(f"✅ '{invalid_input}' → Correctly raised ValueError: {e}")

    return all_passed


def test_bidirectional_mapping_consistency():
    """Test that mappings are bidirectional and consistent."""
    print("\n=== Testing bidirectional mapping consistency ===")

    all_passed = True

    # Test that every legacy status maps to a v2 status and back
    print("\n--- Legacy → V2 → Legacy roundtrip ---")
    for legacy_status, v2_status in LEGACY_TO_V2_MAP.items():
        legacy_back = v2_status_to_legacy(v2_status)
        passed = legacy_back == legacy_status
        all_passed = all_passed and passed
        status_icon = "✅" if passed else "❌"
        print(
            f"{status_icon} '{legacy_status}' → {v2_status} → '{legacy_back}' (expected: '{legacy_status}')"
        )

    # Test that v2 statuses with legacy equivalents map back correctly
    print("\n--- V2 → Legacy → V2 roundtrip (where legacy exists) ---")
    for v2_status, legacy_status in V2_TO_LEGACY_MAP.items():
        if legacy_status is None:
            # Skip v2-only statuses
            continue
        v2_back = legacy_status_to_v2(legacy_status)
        passed = v2_back == v2_status
        all_passed = all_passed and passed
        status_icon = "✅" if passed else "❌"
        print(
            f"{status_icon} {v2_status} → '{legacy_status}' → {v2_back} (expected: {v2_status})"
        )

    return all_passed


def test_all_v2_statuses_covered():
    """Test that all v2 StreamStatus enum values are in the mapping."""
    print("\n=== Testing all v2 statuses are covered ===")

    all_passed = True
    for status in StreamStatus:
        has_legacy = status in V2_TO_LEGACY_MAP
        legacy_value = V2_TO_LEGACY_MAP.get(status, "NOT IN MAP")
        status_icon = "✅" if has_legacy else "❌"
        print(f"{status_icon} {status} → legacy: {legacy_value}")
        all_passed = all_passed and has_legacy

    return all_passed


def main():
    """Run all tests and report results."""
    print("=" * 80)
    print("Legacy Status Compatibility Mapping Tests")
    print("=" * 80)

    test_results = {
        "Legacy → V2 mapping": test_legacy_to_v2_mapping(),
        "V2 → Legacy mapping": test_v2_to_legacy_mapping(),
        "Normalize status input": test_normalize_status_input(),
        "Bidirectional consistency": test_bidirectional_mapping_consistency(),
        "All v2 statuses covered": test_all_v2_statuses_covered(),
    }

    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    all_passed = True
    for test_name, passed in test_results.items():
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} {test_name}: {'PASSED' if passed else 'FAILED'}")
        all_passed = all_passed and passed

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
