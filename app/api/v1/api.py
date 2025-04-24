from fastapi import APIRouter

from app.api.v1.endpoints import posts, users # Import the posts and users routers

api_router_v1 = APIRouter()

# Include routers from endpoints
api_router_v1.include_router(posts.router, prefix="/v1", tags=["Posts"])
api_router_v1.include_router(users.router, prefix="/v1", tags=["Users"]) # Include the users router