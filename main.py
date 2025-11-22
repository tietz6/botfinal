"""
SALESBOT - Training System for Sales Managers
Main FastAPI application with auto-loading of training modules
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("=== SALESBOT Starting ===")
    
    # Initialize database
    from core.state import init_db
    await init_db()
    logger.info("Database initialized")
    
    # Auto-load module routers
    from router_autoload import autoload_routers
    loaded = autoload_routers(app)
    logger.info(f"Loaded {loaded} module routers")
    
    logger.info("=== SALESBOT Ready ===")
    
    yield
    
    # Shutdown
    logger.info("=== SALESBOT Shutting Down ===")


# Create FastAPI app
app = FastAPI(
    title="SALESBOT Training System",
    description="AI-powered training system for sales managers - На Счастье project",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include public API router
from api.public.v1 import router as public_router
app.include_router(public_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SALESBOT Training System",
        "status": "running",
        "project": "На Счастье",
        "endpoints": {
            "health": "/api/public/v1/health",
            "routes": "/api/public/v1/routes_summary"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8080"))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
