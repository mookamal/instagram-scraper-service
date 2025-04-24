# app/schemas/user.py
from pydantic import BaseModel
from typing import Optional

class FollowerCountResponse(BaseModel):
    username: str
    follower_count: Optional[int] = None
    status: str # e.g., "success", "failed_not_found", "error"

    class Config:
        orm_mode = True # Or ConfigDict(from_attributes=True) for Pydantic v2