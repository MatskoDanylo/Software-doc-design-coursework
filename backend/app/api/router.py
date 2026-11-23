from fastapi import APIRouter

from app.api.routes import admin, admin_catalog, admin_video, auth, catalog, playback, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(catalog.router)
api_router.include_router(playback.router)
api_router.include_router(admin.router)
api_router.include_router(admin_catalog.router)
api_router.include_router(admin_video.router)
