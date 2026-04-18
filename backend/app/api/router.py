from fastapi import APIRouter, Depends

from app.api.dependencies import require_auth
from app.api.routers import admin as admin_router
from app.api.routers import auth as auth_router
from app.api.routers import csrf as csrf_router
from app.api.routers import health
from app.api.routers import notifications as notifications_router
from app.api.routers import robots
from app.api.routers import service_orders

_auth = [Depends(require_auth)]

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(csrf_router.router, tags=["segurança"])
api_router.include_router(auth_router.router, tags=["autenticação"])
api_router.include_router(robots.router, tags=["robôs"], dependencies=_auth)
api_router.include_router(service_orders.router, tags=["ordens de serviço"], dependencies=_auth)
api_router.include_router(notifications_router.router, tags=["notificações"], dependencies=_auth)
api_router.include_router(admin_router.router, tags=["administração"])
