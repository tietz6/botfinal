"""User role storage using core.state"""
import logging
from typing import Optional
from core.state import get_state, set_state
from .models import Role

logger = logging.getLogger(__name__)


async def get_user_role(user_id: str) -> Optional[Role]:
    """
    Get user role from storage.
    
    Args:
        user_id: User identifier
        
    Returns:
        User role or None if not set
    """
    key = f"user_role:{user_id}"
    role_str = await get_state(key)
    
    if role_str:
        try:
            return Role(role_str)
        except ValueError:
            logger.warning(f"Invalid role value for user {user_id}: {role_str}")
            return None
    
    return None


async def set_user_role(user_id: str, role: Role) -> None:
    """
    Set user role in storage.
    
    Args:
        user_id: User identifier
        role: Role to assign
    """
    key = f"user_role:{user_id}"
    await set_state(key, role.value)
    logger.info(f"Set role {role.value} for user {user_id}")


async def user_has_role(user_id: str, required_role: Role) -> bool:
    """
    Check if user has required role.
    
    Args:
        user_id: User identifier
        required_role: Required role
        
    Returns:
        True if user has the required role or is admin
    """
    user_role = await get_user_role(user_id)
    
    if not user_role:
        return False
    
    # Admin has access to everything
    if user_role == Role.ADMIN:
        return True
    
    return user_role == required_role
