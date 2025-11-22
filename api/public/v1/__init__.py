"""Public API V1"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.auth import Role, set_user_role, get_user_role

router = APIRouter(prefix="/api/public/v1", tags=["public-v1"])


class SetRoleRequest(BaseModel):
    """Set user role request"""
    user_id: str
    role: str


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SALESBOT",
        "version": "1.0.0"
    }


@router.get("/routes_summary")
async def routes_summary():
    """Summary of all available routes"""
    from main import app
    
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
    
    return {
        "total_routes": len(routes),
        "routes": routes
    }


@router.post("/set_role")
async def set_role(request: SetRoleRequest):
    """
    Set user role.
    
    Used by Telegram bot to assign roles to users during onboarding.
    
    Args:
        request: User ID and role
        
    Returns:
        Success confirmation
    """
    try:
        # Validate role
        try:
            role = Role(request.role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {request.role}. Must be one of: manager, generator, admin"
            )
        
        # Set role
        await set_user_role(request.user_id, role)
        
        return {
            "success": True,
            "user_id": request.user_id,
            "role": role.value,
            "message": f"Role {role.value} assigned to user {request.user_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_role/{user_id}")
async def get_role(user_id: str):
    """
    Get user role.
    
    Args:
        user_id: User identifier
        
    Returns:
        User's assigned role
    """
    try:
        role = await get_user_role(user_id)
        
        if not role:
            return {
                "success": True,
                "user_id": user_id,
                "role": None,
                "message": "No role assigned yet"
            }
        
        return {
            "success": True,
            "user_id": user_id,
            "role": role.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles")
async def list_roles():
    """
    List available roles.
    
    Returns:
        List of available roles with descriptions
    """
    return {
        "success": True,
        "roles": [
            {
                "id": "manager",
                "name": "Менеджер по продажам",
                "description": "Общение с клиентами, продажа услуг"
            },
            {
                "id": "generator",
                "name": "Генератор контента",
                "description": "Создание песен, видео, контента"
            },
            {
                "id": "admin",
                "name": "Руководство",
                "description": "Полный доступ ко всем модулям"
            }
        ]
    }
