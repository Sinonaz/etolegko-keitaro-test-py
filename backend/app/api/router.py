from fastapi import APIRouter

from app.api.routes import campaigns, health, keitaro, offers

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(keitaro.router, tags=["keitaro"])
api_router.include_router(campaigns.router, tags=["campaigns"])
api_router.include_router(offers.router, tags=["offers"])
