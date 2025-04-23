# app/schemas/post.py
from pydantic import BaseModel, Field
from typing import Optional

class LikeResponse(BaseModel):
    """
    Response model for the likes endpoint.
    """
    post_id: str = Field(..., description="The Instagram post ID provided in the request.")
    likes_count: Optional[int] = Field(None, description="The number of likes found for the post. Null if not found or error.")
    status: str = Field(..., description="Indicates if the operation was successful or failed.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "post_id": "DILAYfcKdZa",
                    "likes_count": 12345,
                    "status": "success"
                },
                {
                    "post_id": "nonexistentpost",
                    "likes_count": None,
                    "status": "failed_not_found"
                }
            ]
        }
    }