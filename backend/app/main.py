"""Main FastAPI application entrypoint for Trust Gate."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import init_db
from app.services.device_bridge import device_bridge
from app.routers import (
    verification_router,
    device_router,
    dashboard_router,
    registrations_router,
    review_router,
    demo_router,
    ws_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("trustgate.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event lifecycle."""
    logger.info("Initializing Trust Gate database schema...")
    init_db()

    logger.info("Starting hardware device bridge...")
    device_bridge.start()

    yield

    logger.info("Stopping hardware device bridge...")
    device_bridge.stop()
    logger.info("Trust Gate API shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Physical Identity & Eligibility Verification Gateway API",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits all localhost origins during development & testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploaded files directory for operator inspection
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Include Routers
app.include_router(verification_router)
app.include_router(device_router)
app.include_router(dashboard_router)
app.include_router(registrations_router)
app.include_router(review_router)
app.include_router(demo_router)
app.include_router(ws_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ONLINE",
        "device_id": settings.DEVICE_ID,
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Root"])
async def health_check():
    return {
        "status": "HEALTHY",
        "device_online": device_bridge.state["online"],
        "servo_state": device_bridge.state["servo_state"],
        "lcd_state": device_bridge.state["lcd_state"]
    }
