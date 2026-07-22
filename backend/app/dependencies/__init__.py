"""Dependency injection package."""

from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.container import Container, get_container

__all__ = ["Container", "CurrentUser", "get_container", "require_roles"]
