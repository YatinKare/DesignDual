"""Compatibility layer for legacy stream status values.

Provides bidirectional mapping between v1 statuses (scoping, design, scale, tradeoff)
and v2 statuses (clarify, estimate, design, explain) for backward compatibility.
"""

from __future__ import annotations

from typing import Optional

from app.models.contract_v2 import StreamStatus


# Legacy v1 status values (as strings, not enum)
LEGACY_SCOPING = "scoping"
LEGACY_DESIGN = "design"
LEGACY_SCALE = "scale"
LEGACY_TRADEOFF = "tradeoff"
LEGACY_SYNTHESIZING = "synthesizing"
LEGACY_COMPLETE = "complete"
LEGACY_FAILED = "failed"

# Mapping from legacy v1 status strings to v2 StreamStatus enum values
LEGACY_TO_V2_MAP = {
    LEGACY_SCOPING: StreamStatus.CLARIFY,
    LEGACY_DESIGN: StreamStatus.DESIGN,
    LEGACY_SCALE: StreamStatus.ESTIMATE,
    LEGACY_TRADEOFF: StreamStatus.EXPLAIN,
    LEGACY_SYNTHESIZING: StreamStatus.SYNTHESIZING,
    LEGACY_COMPLETE: StreamStatus.COMPLETE,
    LEGACY_FAILED: StreamStatus.FAILED,
}

# Reverse mapping from v2 StreamStatus enum values to legacy v1 status strings
V2_TO_LEGACY_MAP = {
    StreamStatus.CLARIFY: LEGACY_SCOPING,
    StreamStatus.DESIGN: LEGACY_DESIGN,
    StreamStatus.ESTIMATE: LEGACY_SCALE,
    StreamStatus.EXPLAIN: LEGACY_TRADEOFF,
    StreamStatus.SYNTHESIZING: LEGACY_SYNTHESIZING,
    StreamStatus.COMPLETE: LEGACY_COMPLETE,
    StreamStatus.FAILED: LEGACY_FAILED,
    # New v2-only statuses have no legacy equivalent, return None
    StreamStatus.QUEUED: None,
    StreamStatus.PROCESSING: None,
}


def legacy_status_to_v2(legacy_status: str) -> Optional[StreamStatus]:
    """Convert a legacy v1 status string to v2 StreamStatus enum.

    Args:
        legacy_status: Legacy status string (e.g., "scoping", "scale", "tradeoff")

    Returns:
        Corresponding v2 StreamStatus enum value, or None if invalid

    Example:
        >>> legacy_status_to_v2("scoping")
        StreamStatus.CLARIFY
        >>> legacy_status_to_v2("scale")
        StreamStatus.ESTIMATE
        >>> legacy_status_to_v2("invalid")
        None
    """
    return LEGACY_TO_V2_MAP.get(legacy_status)


def v2_status_to_legacy(v2_status: StreamStatus) -> Optional[str]:
    """Convert a v2 StreamStatus enum to legacy v1 status string.

    Args:
        v2_status: V2 StreamStatus enum value

    Returns:
        Corresponding legacy status string, or None if no legacy equivalent exists

    Example:
        >>> v2_status_to_legacy(StreamStatus.CLARIFY)
        'scoping'
        >>> v2_status_to_legacy(StreamStatus.QUEUED)
        None
    """
    return V2_TO_LEGACY_MAP.get(v2_status)


def normalize_status_input(status: str | StreamStatus) -> StreamStatus:
    """Normalize a status input (string or enum) to v2 StreamStatus enum.

    Accepts both v2 StreamStatus enum values and legacy v1 status strings.
    Useful for API endpoints that need to accept both formats.

    Args:
        status: Status as string (v1 or v2) or StreamStatus enum (v2)

    Returns:
        V2 StreamStatus enum value

    Raises:
        ValueError: If status is invalid or unknown

    Example:
        >>> normalize_status_input("scoping")  # Legacy v1
        StreamStatus.CLARIFY
        >>> normalize_status_input("clarify")  # New v2
        StreamStatus.CLARIFY
        >>> normalize_status_input(StreamStatus.CLARIFY)  # Already v2 enum
        StreamStatus.CLARIFY
    """
    # If already a StreamStatus enum, return as-is
    if isinstance(status, StreamStatus):
        return status

    # If string, try to parse as v2 first
    try:
        return StreamStatus(status)
    except ValueError:
        pass

    # Not a valid v2 status, try legacy mapping
    v2_status = legacy_status_to_v2(status)
    if v2_status is not None:
        return v2_status

    # Invalid status
    raise ValueError(
        f"Invalid status '{status}'. Expected v2 status ({', '.join(s.value for s in StreamStatus)}) "
        f"or legacy v1 status ({', '.join(LEGACY_TO_V2_MAP.keys())})"
    )


__all__ = [
    "LEGACY_TO_V2_MAP",
    "V2_TO_LEGACY_MAP",
    "legacy_status_to_v2",
    "v2_status_to_legacy",
    "normalize_status_input",
]
