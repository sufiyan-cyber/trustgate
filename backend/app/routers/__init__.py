"""Routers package initialization."""
from app.routers.verification import router as verification_router
from app.routers.device import router as device_router
from app.routers.dashboard import router as dashboard_router
from app.routers.registrations import router as registrations_router
from app.routers.review import router as review_router
from app.routers.demo import router as demo_router
from app.routers.ws import router as ws_router

__all__ = [
    "verification_router",
    "device_router",
    "dashboard_router",
    "registrations_router",
    "review_router",
    "demo_router",
    "ws_router",
]
