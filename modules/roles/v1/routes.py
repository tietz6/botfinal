"""Roles API Routes - Manage user roles and access permissions"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.auth.models import Role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roles/v1", tags=["roles"])


class RoleInfo(BaseModel):
    """Role information"""
    role_id: str
    name: str
    description: str
    permissions: list


class MenuAccess(BaseModel):
    """Menu access for a role"""
    role: str
    menu_items: list


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "module": "roles"}


@router.get("/list")
async def list_roles():
    """
    Get list of all available roles in the system.
    
    Returns:
        List of roles with descriptions and permissions
    """
    roles = [
        {
            "role_id": "manager",
            "name": "Менеджер",
            "description": "Менеджер по продажам - работает с клиентами",
            "permissions": [
                "encyclopedia_read",
                "script_lab_full",
                "training_access",
                "song_generator_request",
                "product_modules_all"
            ]
        },
        {
            "role_id": "generator",
            "name": "Генератор",
            "description": "Генератор контента - создает тексты и медиа",
            "permissions": [
                "encyclopedia_read",
                "script_lab_basic",
                "video_prompts_generate",
                "song_generator_create",
                "product_modules_create"
            ]
        },
        {
            "role_id": "admin",
            "name": "Администратор",
            "description": "Руководство - полный доступ",
            "permissions": [
                "all_access",
                "user_management",
                "analytics",
                "system_config"
            ]
        }
    ]
    
    return {
        "success": True,
        "roles": roles,
        "total": len(roles)
    }


@router.get("/role/{role_id}")
async def get_role(role_id: str):
    """
    Get detailed information about a specific role.
    
    Args:
        role_id: Role identifier (manager, generator, admin)
        
    Returns:
        Detailed role information
    """
    roles_map = {
        "manager": {
            "role_id": "manager",
            "name": "Менеджер",
            "description": "Менеджер по продажам - работает с клиентами",
            "permissions": [
                "encyclopedia_read",
                "script_lab_full",
                "training_access",
                "song_generator_request",
                "product_modules_all"
            ],
            "access": {
                "encyclopedia": True,
                "script_lab": True,
                "training": True,
                "song_generator": True,
                "video_prompts": True,
                "photo_animation": True,
                "analytics": False,
                "user_management": False
            }
        },
        "generator": {
            "role_id": "generator",
            "name": "Генератор",
            "description": "Генератор контента - создает тексты и медиа",
            "permissions": [
                "encyclopedia_read",
                "script_lab_basic",
                "video_prompts_generate",
                "song_generator_create",
                "product_modules_create"
            ],
            "access": {
                "encyclopedia": True,
                "script_lab": True,  # Only basic
                "training": False,
                "song_generator": True,
                "video_prompts": True,
                "photo_animation": True,
                "analytics": False,
                "user_management": False
            }
        },
        "admin": {
            "role_id": "admin",
            "name": "Администратор",
            "description": "Руководство - полный доступ",
            "permissions": [
                "all_access",
                "user_management",
                "analytics",
                "system_config"
            ],
            "access": {
                "encyclopedia": True,
                "script_lab": True,
                "training": True,
                "song_generator": True,
                "video_prompts": True,
                "photo_animation": True,
                "analytics": True,
                "user_management": True
            }
        }
    }
    
    role_data = roles_map.get(role_id)
    if not role_data:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{role_id}' not found"
        )
    
    return {
        "success": True,
        "role": role_data
    }


@router.get("/menu")
async def get_menu(role: Optional[str] = Query(None, description="User role")):
    """
    Get menu structure based on user role.
    
    Args:
        role: User role (manager, generator, admin)
        
    Returns:
        Menu items available for the role
    """
    if not role:
        raise HTTPException(
            status_code=400,
            detail="Role parameter is required"
        )
    
    # Validate role
    if role not in ["manager", "generator", "admin"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {role}. Must be one of: manager, generator, admin"
        )
    
    # Define menu structure for each role
    menus = {
        "manager": [
            {
                "id": "encyclopedia",
                "name": "📘 Энциклопедия",
                "description": "База знаний и обучающие материалы",
                "icon": "📘",
                "route": "/encyclopedia/v1/pages",
                "enabled": True
            },
            {
                "id": "script_lab",
                "name": "🧪 Script Lab",
                "description": "Анализ и улучшение скриптов продаж",
                "icon": "🧪",
                "route": "/script_lab/v1/analyze",
                "enabled": True
            },
            {
                "id": "training",
                "name": "📚 Школа продаж",
                "description": "Обучение техникам продаж",
                "icon": "📚",
                "route": "/encyclopedia/v1/page/sales_basics",
                "enabled": True
            },
            {
                "id": "song_generator",
                "name": "🎤 Генератор песен",
                "description": "Создание персонализированных песен",
                "icon": "🎤",
                "route": "/song_generator/v1/generate",
                "enabled": True
            },
            {
                "id": "video_prompts",
                "name": "🎬 Видео-промты",
                "description": "Генерация промтов для видео",
                "icon": "🎬",
                "route": "/video_prompt_generator/v1/generate",
                "enabled": True
            },
            {
                "id": "photo_animation",
                "name": "📸 Оживление фото",
                "description": "Анимация фотографий",
                "icon": "📸",
                "route": "/photo_animation/v1/animate",
                "enabled": True
            }
        ],
        "generator": [
            {
                "id": "encyclopedia",
                "name": "📘 Энциклопедия",
                "description": "База знаний (базовый доступ)",
                "icon": "📘",
                "route": "/encyclopedia/v1/pages",
                "enabled": True
            },
            {
                "id": "script_lab",
                "name": "🧪 Script Lab",
                "description": "Анализ скриптов (базовый)",
                "icon": "🧪",
                "route": "/script_lab/v1/analyze",
                "enabled": True
            },
            {
                "id": "song_generator",
                "name": "🎤 Генератор песен",
                "description": "Создание текстов песен",
                "icon": "🎤",
                "route": "/song_generator/v1/generate",
                "enabled": True
            },
            {
                "id": "video_prompts",
                "name": "🎬 Генератор видео-промтов",
                "description": "Создание промтов для Sora/Veo",
                "icon": "🎬",
                "route": "/video_prompt_generator/v1/generate",
                "enabled": True
            },
            {
                "id": "photo_animation",
                "name": "📸 Оживление фото",
                "description": "Анимация фотографий",
                "icon": "📸",
                "route": "/photo_animation/v1/animate",
                "enabled": True
            }
        ],
        "admin": [
            {
                "id": "encyclopedia",
                "name": "📘 Энциклопедия",
                "description": "Полный доступ к базе знаний",
                "icon": "📘",
                "route": "/encyclopedia/v1/pages",
                "enabled": True
            },
            {
                "id": "script_lab",
                "name": "🧪 Script Lab",
                "description": "Полный доступ к анализу скриптов",
                "icon": "🧪",
                "route": "/script_lab/v1/analyze",
                "enabled": True
            },
            {
                "id": "training",
                "name": "📚 Школа продаж",
                "description": "Полный доступ к обучению",
                "icon": "📚",
                "route": "/encyclopedia/v1/page/sales_basics",
                "enabled": True
            },
            {
                "id": "song_generator",
                "name": "🎤 Генератор песен",
                "description": "Создание персонализированных песен",
                "icon": "🎤",
                "route": "/song_generator/v1/generate",
                "enabled": True
            },
            {
                "id": "video_prompts",
                "name": "🎬 Видео-промты",
                "description": "Генерация промтов для видео",
                "icon": "🎬",
                "route": "/video_prompt_generator/v1/generate",
                "enabled": True
            },
            {
                "id": "photo_animation",
                "name": "📸 Оживление фото",
                "description": "Анимация фотографий",
                "icon": "📸",
                "route": "/photo_animation/v1/animate",
                "enabled": True
            },
            {
                "id": "analytics",
                "name": "📊 Аналитика",
                "description": "Статистика и отчеты",
                "icon": "📊",
                "route": "/analytics/v1/dashboard",
                "enabled": True
            },
            {
                "id": "users",
                "name": "👥 Управление пользователями",
                "description": "Управление командой",
                "icon": "👥",
                "route": "/users/v1/list",
                "enabled": True
            }
        ]
    }
    
    menu_items = menus.get(role, [])
    
    return {
        "success": True,
        "role": role,
        "menu": menu_items,
        "total_items": len(menu_items)
    }


@router.get("/check-access")
async def check_access(
    role: str = Query(..., description="User role"),
    resource: str = Query(..., description="Resource to check access for")
):
    """
    Check if a role has access to a specific resource.
    
    Args:
        role: User role (manager, generator, admin)
        resource: Resource identifier (e.g., 'encyclopedia', 'script_lab')
        
    Returns:
        Access status
    """
    # Define access matrix
    access_matrix = {
        "manager": {
            "encyclopedia": True,
            "script_lab": True,
            "training": True,
            "song_generator": True,
            "video_prompts": True,
            "photo_animation": True,
            "analytics": False,
            "user_management": False
        },
        "generator": {
            "encyclopedia": True,
            "script_lab": True,  # Basic only
            "training": False,
            "song_generator": True,
            "video_prompts": True,
            "photo_animation": True,
            "analytics": False,
            "user_management": False
        },
        "admin": {
            "encyclopedia": True,
            "script_lab": True,
            "training": True,
            "song_generator": True,
            "video_prompts": True,
            "photo_animation": True,
            "analytics": True,
            "user_management": True
        }
    }
    
    if role not in access_matrix:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {role}"
        )
    
    role_access = access_matrix[role]
    has_access = role_access.get(resource, False)
    
    return {
        "success": True,
        "role": role,
        "resource": resource,
        "has_access": has_access,
        "level": "full" if has_access else "none"
    }
