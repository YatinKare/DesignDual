"""FastAPI application entrypoint for DesignDual."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import dashboard_router, problems_router, submissions_router

# Load .env from project root first (contains GOOGLE_API_KEY and other secrets),
# then backend/.env for backend-specific config (override=False keeps root values).
BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_ROOT / ".env", override=False)


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

    app.include_router(dashboard_router)
    app.include_router(problems_router)
    app.include_router(submissions_router)

    return app


app = create_app()

__all__ = ["app", "create_app"]
