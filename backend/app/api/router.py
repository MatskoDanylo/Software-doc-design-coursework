from fastapi import APIRouter

from app.api.routes import admin, admin_catalog, auth, catalog, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(catalog.router)
api_router.include_router(admin.router)
api_router.include_router(admin_catalog.router)
