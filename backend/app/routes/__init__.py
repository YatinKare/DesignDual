"""API route modules."""

from .dashboard import router as dashboard_router
from .problems import router as problems_router
from .submissions import router as submissions_router

__all__ = ["dashboard_router", "problems_router", "submissions_router"]
