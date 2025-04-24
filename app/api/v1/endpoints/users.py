# app/api/v1/endpoints/users.py
from fastapi import APIRouter, HTTPException, Depends, Path, status
from typing import Optional

# Assuming the scraper class and response schema will be created/available
from app.services.instagram_scraper import InstagramUserScraper # Import the actual scraper
from app.schemas.user import FollowerCountResponse # Placeholder
from app.core.security import verify_api_key
from app.core.config import settings

router = APIRouter()

# Instantiate the scraper. Consider pooling or lifespan management for high traffic.
scraper = InstagramUserScraper(proxies=settings.PROXIES)

@router.get(
    "/users/{username}/follower_count",
    response_model=FollowerCountResponse,
    summary="Get Follower Count for an Instagram User",
    description="Retrieves the approximate number of followers for a public Instagram user profile. Requires a valid API Key.",
    dependencies=[Depends(verify_api_key)]
)
async def get_user_follower_count(
    username: str = Path(..., description="The username of the Instagram user.", min_length=1)
) -> FollowerCountResponse:
    """
    Endpoint to fetch the number of followers for a given Instagram username.
    """
    follower_count: Optional[int] = None
    try:
        # Execute the scraping task to get the follower count
        follower_count = scraper.get_follower_count(username)

        if follower_count is not None:
            return FollowerCountResponse(username=username, follower_count=follower_count, status="success")
        else:
            # Handle cases where follower count couldn't be retrieved (private, non-existent, scraping failed)
            # Option 1: Raise 404
            # raise HTTPException(
            #     status_code=status.HTTP_404_NOT_FOUND,
            #     detail=f"Could not retrieve follower count for username '{username}'. User may be private, non-existent, or scraping failed.",
            # )
            # Option 2: Return 200 OK with status field
            return FollowerCountResponse(username=username, follower_count=None, status="failed_not_found")

    except Exception as e:
        # Log the error ideally
        # logger.error(f"Unexpected error scraping followers for {username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while trying to scrape followers for username '{username}'.",
        )