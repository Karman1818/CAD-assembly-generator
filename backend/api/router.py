from fastapi import APIRouter
from backend.api.endpoints import step, assembly

api_router = APIRouter()
api_router.include_router(step.router, prefix="/step", tags=["step"])
api_router.include_router(assembly.router, prefix="/assembly", tags=["assembly"])
