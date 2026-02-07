"""Database helpers for the DesignDual backend."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

BACKEND_DIR: Final[Path] = Path(__file__).resolve().parents[2]
REPO_ROOT: Final[Path] = BACKEND_DIR.parent

DEFAULT_DATABASE_URL: Final[str] = os.environ.get(
    "DATABASE_URL", "sqlite+aiosqlite:///./backend/data/designdual.db"
)


def resolve_database_path(database_url: str | None = None) -> Path:
    """Return the filesystem path for a sqlite(+aiosqlite) URL."""

    url = (database_url or DEFAULT_DATABASE_URL).strip()
    prefixes = (
        "sqlite+aiosqlite:///",
        "sqlite+aiosqlite://",
        "sqlite:///",
        "sqlite://",
    )
    for prefix in prefixes:
        if url.startswith(prefix):
            raw_path = url[len(prefix) :]
            break
    else:  # pragma: no cover - defensive branch
        raise ValueError(
            "DATABASE_URL must start with sqlite:/// or sqlite+aiosqlite:/// "
            f"(got {database_url!r})"
        )

    if raw_path == ":memory:":
        raise ValueError("Persistent database path required; ':memory:' unsupported.")

    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path

    # Resolve relative paths against the repo root so shared defaults work everywhere.
    return (REPO_ROOT / path).resolve()


__all__ = ["DEFAULT_DATABASE_URL", "resolve_database_path"]
