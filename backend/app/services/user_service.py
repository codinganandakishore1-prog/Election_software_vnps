"""User management service."""

from __future__ import annotations

import re

from election_platform.enums.roles import UserRole

from app.database.seeds import ROLE_IDS, new_uuid
from app.exceptions.base import NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserCreate,
    UserPasswordChange,
    UserPasswordReset,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)
from app.security.password import PasswordHasher
from app.services.base import BaseService

_PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$")


class UserService(BaseService):
    """Handles user CRUD and password operations."""

    def __init__(
        self,
        user_repository: UserRepository,
        audit_log_repository: AuditLogRepository,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.audit_log_repository = audit_log_repository
        self.password_hasher = password_hasher or PasswordHasher()

    def get_current_user(self, user_id: str) -> UserResponse:
        user = self.user_repository.get_by_id_with_role(user_id)
        if user is None or user.deleted_at is not None:
            raise NotFoundError("User not found")
        return self._to_response(user)

    def list_users(self) -> list[UserResponse]:
        users = self.user_repository.list_active()
        return [self._to_response(user) for user in users if user.deleted_at is None]

    def create_user(self, payload: UserCreate, *, actor_id: str | None = None) -> UserResponse:
        self._validate_password(payload.password)
        if self.user_repository.get_by_username(payload.username):
            raise ValidationError("Username already exists")
        if payload.email and self.user_repository.get_by_email(payload.email):
            raise ValidationError("Email already exists")

        role_id = self._resolve_role_id(payload.role)
        user = User(
            id=new_uuid(),
            username=payload.username.strip(),
            full_name=payload.full_name,
            email=payload.email,
            password_hash=self.password_hasher.hash_password(payload.password),
            role_id=role_id,
            active=True,
        )
        self.user_repository.add(user)
        self._audit(actor_id, "User Created", {"username": user.username, "role": payload.role})
        self.user_repository.commit()
        return self._to_response(self.user_repository.get_by_id_with_role(user.id))

    def update_user(self, user_id: str, payload: UserUpdate, *, actor_id: str | None = None) -> UserResponse:
        user = self._get_user_or_raise(user_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise ValidationError("No fields provided to update")

        if "email" in updates and updates["email"]:
            existing = self.user_repository.get_by_email(updates["email"])
            if existing and existing.id != user.id:
                raise ValidationError("Email already exists")

        if "role" in updates and updates["role"] is not None:
            user.role_id = self._resolve_role_id(updates.pop("role"))

        for field, value in updates.items():
            setattr(user, field, value)

        self._audit(actor_id, "User Updated", {"user_id": user.id, **updates})
        self.user_repository.commit()
        return self._to_response(self.user_repository.get_by_id_with_role(user.id))

    def update_own_profile(
        self,
        user_id: str,
        payload: UserProfileUpdate,
        *,
        actor_id: str | None = None,
    ) -> UserResponse:
        user = self._get_user_or_raise(user_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise ValidationError("No fields provided to update")

        if "email" in updates and updates["email"]:
            existing = self.user_repository.get_by_email(updates["email"])
            if existing and existing.id != user.id:
                raise ValidationError("Email already exists")

        for field, value in updates.items():
            setattr(user, field, value)

        self._audit(actor_id or user_id, "Profile Updated", {"user_id": user.id, **updates})
        self.user_repository.commit()
        return self._to_response(self.user_repository.get_by_id_with_role(user.id))

    def reset_password(self, user_id: str, payload: UserPasswordReset, *, actor_id: str | None = None) -> None:
        user = self._get_user_or_raise(user_id)
        self._validate_password(payload.password)
        user.password_hash = self.password_hasher.hash_password(payload.password)
        self._audit(actor_id, "Password Reset", {"user_id": user.id})
        self.user_repository.commit()

    def change_password(self, user_id: str, payload: UserPasswordChange) -> None:
        user = self._get_user_or_raise(user_id)
        if not self.password_hasher.verify_password(payload.old_password, user.password_hash):
            raise ValidationError("Current password is incorrect")
        self._validate_password(payload.new_password)
        if payload.old_password == payload.new_password:
            raise ValidationError("New password must be different from the current password")
        user.password_hash = self.password_hasher.hash_password(payload.new_password)
        self._audit(user_id, "Password Changed", {"user_id": user.id})
        self.user_repository.commit()

    def disable_user(self, user_id: str, *, actor_id: str | None = None) -> UserResponse:
        user = self._get_user_or_raise(user_id)
        user.active = False
        self._audit(actor_id, "User Disabled", {"user_id": user.id})
        self.user_repository.commit()
        return self._to_response(self.user_repository.get_by_id_with_role(user.id))

    def _get_user_or_raise(self, user_id: str) -> User:
        user = self.user_repository.get_by_id(user_id)
        if user is None or user.deleted_at is not None:
            raise NotFoundError("User not found")
        return user

    @staticmethod
    def _resolve_role_id(role_name: str) -> str:
        normalized = role_name.strip()
        for role_enum, role_id in ROLE_IDS.items():
            if role_enum.value == normalized:
                return role_id
        raise ValidationError(f"Unsupported role: {role_name}")

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        if not _PASSWORD_PATTERN.match(password):
            raise ValidationError(
                "Password must include uppercase, lowercase, number, and special character"
            )

    @staticmethod
    def _to_response(user: User | None) -> UserResponse:
        if user is None:
            raise NotFoundError("User not found")
        return UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role.role_name if user.role else UserRole.VIEWER.value,
            active=user.active,
        )

    def _audit(self, actor_id: str | None, action: str, details: dict) -> None:
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=actor_id,
                action=action,
                module="users",
                new_value=str(details),
            )
        )
