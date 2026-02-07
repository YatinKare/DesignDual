"""API route modules."""

from .problems import router as problems_router
from .submissions import router as submissions_router

__all__ = ["problems_router", "submissions_router"]
