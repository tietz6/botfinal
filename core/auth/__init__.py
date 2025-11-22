"""Authentication and authorization module"""
from .models import Role, User
from .storage import get_user_role, set_user_role, user_has_role
from .deps import get_current_user, require_role

__all__ = [
    "Role",
    "User",
    "get_user_role",
    "set_user_role",
    "user_has_role",
    "get_current_user",
    "require_role"
]
