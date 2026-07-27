"""Shared FastAPI dependencies."""

from app.auth.dependencies import get_current_user
from app.database.connection import get_db

__all__ = ["get_current_user", "get_db"]
