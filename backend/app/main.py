"""FastAPI application entrypoint for DesignDual."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")


def _parse_origins(raw_value: str | None) -> List[str]:
    if not raw_value:
        return []
    origins = [origin.strip() for origin in raw_value.split(",")]
    return [origin for origin in origins if origin]


def create_app() -> FastAPI:
    app = FastAPI(title="DesignDual API", version="0.1.0")

    origins = _parse_origins(os.getenv("FRONTEND_ORIGIN", ""))
    if origins:
        allow_credentials = "*" not in origins
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app


app = create_app()

__all__ = ["app", "create_app"]
