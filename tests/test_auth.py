"""Tests for authorization service."""

from __future__ import annotations

import pytest

from services.auth import (
    UserRole,
    can_administer,
    can_create_project,
    can_record_outcome,
    can_view_employee_details,
    can_view_hindsight,
    has_role,
    require_role,
)


class TestRoleHierarchy:
    def test_admin_has_all_access(self) -> None:
        assert has_role(UserRole.ADMIN, UserRole.VIEWER)
        assert has_role(UserRole.ADMIN, UserRole.MANAGER)
        assert has_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER)
        assert has_role(UserRole.ADMIN, UserRole.HR)
        assert has_role(UserRole.ADMIN, UserRole.ADMIN)

    def test_viewer_has_minimal_access(self) -> None:
        assert has_role(UserRole.VIEWER, UserRole.VIEWER)
        assert not has_role(UserRole.VIEWER, UserRole.MANAGER)
        assert not has_role(UserRole.VIEWER, UserRole.ADMIN)

    def test_project_manager_access(self) -> None:
        assert can_create_project(UserRole.PROJECT_MANAGER)
        assert can_record_outcome(UserRole.PROJECT_MANAGER)
        assert not can_administer(UserRole.PROJECT_MANAGER)

    def test_manager_can_view_hindsight(self) -> None:
        assert can_view_hindsight(UserRole.MANAGER)
        assert not can_view_hindsight(UserRole.VIEWER)

    def test_viewer_cannot_view_employee_details(self) -> None:
        assert not can_view_employee_details(UserRole.VIEWER)
        assert can_view_employee_details(UserRole.MANAGER)


class TestRequireRoleDecorator:
    def test_allows_sufficient_role(self) -> None:
        @require_role(UserRole.MANAGER)
        def protected(user_role: UserRole) -> str:
            return "ok"

        assert protected(user_role=UserRole.MANAGER) == "ok"
        assert protected(user_role=UserRole.ADMIN) == "ok"

    def test_raises_for_insufficient_role(self) -> None:
        @require_role(UserRole.ADMIN)
        def admin_only(user_role: UserRole) -> str:
            return "admin"

        with pytest.raises(PermissionError):
            admin_only(user_role=UserRole.VIEWER)

    def test_raises_for_default_viewer(self) -> None:
        @require_role(UserRole.MANAGER)
        def manager_only(user_role: UserRole = UserRole.VIEWER) -> str:
            return "ok"

        with pytest.raises(PermissionError):
            manager_only()
