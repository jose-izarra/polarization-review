from pydantic import BaseModel, Field
from typing import Literal

class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    time_filter: Literal["day", "week", "month"] = "week"
    max_posts: int = Field(30, ge=1, le=200)
    max_comments_per_post: int = Field(10, ge=1, le=200)
