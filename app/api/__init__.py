"""API routers package."""

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.query import router as query_router
from app.api.upload import router as upload_router

__all__ = ["analytics_router", "auth_router", "query_router", "upload_router"]