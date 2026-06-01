"""Router agregador de la API v1."""
from fastapi import APIRouter

from app.api.v1.endpoints.bot_simple import router as bot_simple_router
from app.api.v1.endpoints.bot_avanzado import router as bot_avanzado_router

api_router = APIRouter()
api_router.include_router(bot_simple_router)
api_router.include_router(bot_avanzado_router)
