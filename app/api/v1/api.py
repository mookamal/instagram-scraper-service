from fastapi import APIRouter

from app.api.v1.endpoints import posts # Import the posts router

api_router_v1 = APIRouter()

# Include routers from endpoints
api_router_v1.include_router(posts.router, prefix="/v1", tags=["Posts"])