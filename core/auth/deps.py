"""FastAPI dependencies for authentication"""
from typing import Optional
from fastapi import Header, HTTPException
from .models import Role, User
from .storage import get_user_role


async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    x_role: Optional[str] = Header(None)
) -> User:
    """
    Get current user from headers.
    For now, accepts user_id and role from headers.
    In production, this should validate JWT tokens.
    
    Args:
        x_user_id: User ID from header
        x_role: Role from header (optional, will check storage if not provided)
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user_id is not provided
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    # Try to get role from header first, then from storage
    if x_role:
        try:
            role = Role(x_role)
        except ValueError:
            # If invalid role in header, try storage
            role = await get_user_role(x_user_id)
            if not role:
                role = Role.MANAGER  # Default role
    else:
        role = await get_user_role(x_user_id)
        if not role:
            role = Role.MANAGER  # Default role
    
    return User(user_id=x_user_id, role=role)


def require_role(required_role: Role):
    """
    Dependency factory to require specific role.
    
    Args:
        required_role: Required role
        
    Returns:
        Dependency function
    """
    async def role_checker(user: User = Header(None)) -> User:
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Admin has access to everything
        if user.role == Role.ADMIN:
            return user
        
        if user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Role {required_role.value} required"
            )
        
        return user
    
    return role_checker
