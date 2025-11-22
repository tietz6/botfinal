"""Authentication models"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Role(str, Enum):
    """User roles in the system"""
    MANAGER = "manager"
    GENERATOR = "generator"
    ADMIN = "admin"


class User(BaseModel):
    """User model"""
    user_id: str
    role: Role
    name: Optional[str] = None
    telegram_id: Optional[int] = None
