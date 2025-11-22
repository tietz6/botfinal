"""Public API V1"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/public/v1", tags=["public-v1"])


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
