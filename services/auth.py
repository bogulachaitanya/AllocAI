"""Authorization service.

Two-layer protection strategy:
    Layer 1: @require_role decorator  — fast gate on entry to a function
    Layer 2: ServiceGuard            — explicit boundary check inside service methods

The decorator alone is not sufficient because it can be bypassed if a method
is called from another service without going through the decorated wrapper.

Enforced data-access scopes:
    ADMIN           → full access, including diagnostics and user management
    HR              → employee details, performance records, all projects
    PROJECT_MANAGER → candidates for assigned projects, authorized Hindsight memories
    MANAGER         → employee details, Hindsight memories, own team
    VIEWER          → aggregated/anonymized data only, no Hindsight

Pipeline:
    UI
     ↓
    Service authorization  (ServiceGuard.require + capability checks)
     ↓
    Repository
     ↓
    Database / Hindsight
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from enum import StrEnum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class UserRole(StrEnum):
    ADMIN = "admin"
    HR = "hr"
    PROJECT_MANAGER = "project_manager"
    MANAGER = "manager"
    VIEWER = "viewer"


# Role hierarchy — higher index = more access
_ROLE_LEVEL: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.MANAGER: 1,
    UserRole.PROJECT_MANAGER: 2,
    UserRole.HR: 3,
    UserRole.ADMIN: 4,
}


# ── Core predicate ────────────────────────────────────────────────────────────


def has_role(user_role: UserRole, required_role: UserRole) -> bool:
    """Return True if user_role meets or exceeds required_role."""
    return _ROLE_LEVEL.get(user_role, -1) >= _ROLE_LEVEL.get(required_role, 999)


# ── Decorator (Layer 1 — entry gate) ─────────────────────────────────────────


def require_role(required: UserRole) -> Callable:
    """Decorator: raise PermissionError if caller lacks the required role.

    Use as a fast entry gate. Does NOT replace service-boundary checks.
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user_role: UserRole = kwargs.get("user_role", UserRole.VIEWER)
            if not has_role(user_role, required):
                raise PermissionError(
                    f"Action requires role '{required.value}' but caller has '{user_role.value}'"
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# ── ServiceGuard (Layer 2 — explicit boundary enforcement) ────────────────────


class ServiceGuard:
    """Explicit authorization boundary for service methods.

    Usage inside any service method:
        guard = ServiceGuard(user_role)
        guard.require_employee_access()       # raises if insufficient role
        guard.require_hindsight_access()      # raises if insufficient role

    This cannot be bypassed by calling the method from another service.
    """

    def __init__(self, user_role: UserRole) -> None:
        self._role = user_role

    def require(self, needed: UserRole, context: str = "") -> None:
        """Raise PermissionError if the current role is insufficient."""
        if not has_role(self._role, needed):
            msg = (
                f"Service boundary: '{needed.value}' required"
                + (f" ({context})" if context else "")
                + f", caller has '{self._role.value}'"
            )
            logger.warning("Authorization denied: %s", msg)
            raise PermissionError(msg)

    def require_employee_access(self) -> None:
        """Enforce: only MANAGER+ can access individual employee details."""
        self.require(UserRole.MANAGER, "employee details")

    def require_hindsight_access(self) -> None:
        """Enforce: only MANAGER+ can retrieve Hindsight memories."""
        self.require(UserRole.MANAGER, "Hindsight memory")

    def require_project_creation(self) -> None:
        """Enforce: only PROJECT_MANAGER+ can create projects."""
        self.require(UserRole.PROJECT_MANAGER, "project creation")

    def require_outcome_recording(self) -> None:
        """Enforce: only PROJECT_MANAGER+ can record project outcomes."""
        self.require(UserRole.PROJECT_MANAGER, "outcome recording")

    def require_admin(self) -> None:
        """Enforce: only ADMIN can perform administrative operations."""
        self.require(UserRole.ADMIN, "admin operation")


# ── Capability helpers (used by EvidenceService and UI) ──────────────────────


def can_view_employee_details(role: UserRole) -> bool:
    return has_role(role, UserRole.MANAGER)


def can_create_project(role: UserRole) -> bool:
    return has_role(role, UserRole.PROJECT_MANAGER)


def can_record_outcome(role: UserRole) -> bool:
    return has_role(role, UserRole.PROJECT_MANAGER)


def can_view_hindsight(role: UserRole) -> bool:
    return has_role(role, UserRole.MANAGER)


def can_administer(role: UserRole) -> bool:
    return has_role(role, UserRole.ADMIN)
