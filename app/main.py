from fastapi import FastAPI
from app.api.v1.api import api_router_v1 # Import the v1 router aggregator
from app.core.config import settings # To potentially use settings during startup

# Initialize FastAPI app
app = FastAPI(
    title="Instagram Scraper Service",
    description="An API service to scrape data from Instagram (use responsibly).",
    version="0.1.0",
    # Add lifespan events here later if needed for resource management
    # lifespan=...
)

# Include the API routers
app.include_router(api_router_v1, prefix="/api") # Add /api prefix to all v1 routes

# Root endpoint for basic health check or info
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Instagram Scraper Service API"}

# Example: Show loaded settings (for debugging, remove in production)
@app.get("/debug-settings", tags=["Debug"])
async def show_settings():
    # Be careful exposing settings, especially API keys, even in debug endpoints
    return {
        "scraper_headless": settings.SCRAPER_HEADLESS,
        "api_keys_loaded": bool(settings.ALLOWED_API_KEYS),
        "number_of_keys": len(settings.ALLOWED_API_KEYS)
        # Avoid returning the actual keys: "allowed_keys": list(settings.ALLOWED_API_KEYS)
    }

# Add other global configurations or middleware if needed

# Note: uvicorn command will run this 'app' object