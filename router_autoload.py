"""
Router auto-loader for SALESBOT modules.
Scans modules/ folder and automatically registers all routers.
"""
import os
import importlib
import logging
from pathlib import Path
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def discover_modules(base_path: Path) -> dict:
    """
    Discover all modules with routes.py in modules/ folder.
    
    Returns:
        dict: {module_name: module_path}
    """
    modules = {}
    
    if not base_path.exists():
        logger.warning(f"Modules folder not found: {base_path}")
        return modules
    
    logger.info(f"FS-scan modules folder: {base_path}")
    
    # Scan for module/version/routes.py pattern
    for module_dir in base_path.iterdir():
        if not module_dir.is_dir() or module_dir.name.startswith("_"):
            continue
        
        # Check for versioned modules (e.g., master_path/v1)
        for version_dir in module_dir.iterdir():
            if version_dir.is_dir() and version_dir.name.startswith("v"):
                routes_file = version_dir / "routes.py"
                if routes_file.exists():
                    module_name = f"{module_dir.name}_{version_dir.name}"
                    module_path = f"modules.{module_dir.name}.{version_dir.name}.routes"
                    modules[module_name] = module_path
                    logger.info(f"Discovered module: {module_name} -> {module_path}")
    
    logger.info(f"Discovered module commands: {list(modules.keys())}")
    return modules


def load_module_router(module_path: str):
    """
    Load router from module path.
    
    Args:
        module_path: Python module path (e.g., 'modules.master_path.v1.routes')
    
    Returns:
        APIRouter or None
    """
    try:
        module = importlib.import_module(module_path)
        if hasattr(module, "router"):
            logger.info(f"Loaded router from {module_path}")
            return module.router
        else:
            logger.warning(f"Module {module_path} has no 'router' attribute")
            return None
    except Exception as e:
        logger.error(f"Failed to load module {module_path}: {e}")
        return None


def autoload_routers(app: FastAPI):
    """
    Auto-load all module routers into FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    base_path = Path(__file__).parent / "modules"
    modules = discover_modules(base_path)
    
    loaded_count = 0
    for module_name, module_path in modules.items():
        router = load_module_router(module_path)
        if router:
            app.include_router(router)
            loaded_count += 1
            logger.info(f"Registered router: {module_name}")
    
    logger.info(f"Total routers loaded: {loaded_count}")
    return loaded_count
