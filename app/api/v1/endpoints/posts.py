# app/api/v1/endpoints/posts.py
from fastapi import APIRouter, HTTPException, Depends, Path, status

# Assuming the scraper class is correctly placed
from app.services.instagram_scraper import InstagramPostScraper
from app.schemas.post import LikeResponse # Import the response schema
from app.core.security import verify_api_key # Import the security dependency
from app.core.config import settings # Import settings to get headless config

router = APIRouter()
scraper = InstagramPostScraper(proxies=settings.PROXIES)

@router.get(
    "/posts/{post_id}/likes",
    response_model=LikeResponse,
    summary="Get Like Count for an Instagram Post",
    description="Retrieves the approximate number of likes for a public Instagram post using its shortcode (post ID). Requires a valid API Key.",
    dependencies=[Depends(verify_api_key)] # Apply API key security
)
async def get_post_likes(
    post_id: str = Path(..., description="The shortcode (ID) of the Instagram post (e.g., DILAYfcKdZa).", min_length=5)
) -> LikeResponse:
    """
    Endpoint to fetch the number of likes for a given Instagram post ID.
    """
    post_url = f"https://www.instagram.com/p/{post_id}/"

    # Instantiate scraper for this request using headless setting from config
    # Note: Consider instance pooling or lifespan management for high traffic
    likes = None
    try:
        # Execute the scraping task
        likes = scraper.get_likes(post_id) # This method handles driver creation/closing internally now

        if likes is not None:
            return LikeResponse(post_id=post_id, likes_count=likes, status="success")
        else:
            # If scraper returns None, it means it couldn't find the likes count
            # This could be due to post not existing, private post, network issue, or scraping blocked.
            # Returning 404 is a common practice, although the exact reason is unknown.
            # raise HTTPException( # Option 1: Raise 404
            #     status_code=status.HTTP_404_NOT_FOUND,
            #     detail=f"Could not retrieve likes for post ID '{post_id}'. Post may be private, non-existent, or scraping failed.",
            # )
             return LikeResponse(post_id=post_id, likes_count=None, status="failed_not_found") # Option 2: Return 200 OK with status field


    except Exception as e:
        # Catch any unexpected errors during scraper instantiation or execution
        # Log the error ideally
        # logger.error(f"Unexpected error scraping {post_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while trying to scrape likes for post ID '{post_id}'.",
        )
    # No finally block needed here IF get_likes guarantees driver closure internally.
    # If get_likes could potentially leak the driver on error before the finally block
    # inside it runs, you might need a try/finally here around scraper usage.