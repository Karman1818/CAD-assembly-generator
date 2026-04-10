from fastapi import APIRouter
from backend.api.endpoints import step

api_router = APIRouter()
api_router.include_router(step.router, prefix="/step", tags=["step"])
