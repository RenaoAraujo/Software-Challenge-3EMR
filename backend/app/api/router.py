from fastapi import APIRouter

from app.api.routers import csrf as csrf_router
from app.api.routers import health
from app.api.routers import robots
from app.api.routers import service_orders

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(csrf_router.router, tags=["segurança"])
api_router.include_router(robots.router, tags=["robôs"])
api_router.include_router(service_orders.router, tags=["ordens de serviço"])
