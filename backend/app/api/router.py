from fastapi import APIRouter

from app.api.routes import (
    admin, admin_billing, admin_catalog, admin_settings, admin_video, auth, billing, catalog, favorites, history, notifications,
    playback, plans, recommendations, subscriptions, users,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(catalog.router)
api_router.include_router(recommendations.router)
api_router.include_router(playback.router)
api_router.include_router(favorites.router)
api_router.include_router(history.router)
api_router.include_router(subscriptions.router)
api_router.include_router(plans.router)
api_router.include_router(billing.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
api_router.include_router(admin_catalog.router)
api_router.include_router(admin_video.router)
api_router.include_router(admin_billing.router)
api_router.include_router(admin_settings.router)
