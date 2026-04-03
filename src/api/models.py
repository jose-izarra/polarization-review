from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    time_filter: Literal["day", "week", "month"] = "month"
    max_posts: int = Field(30, ge=1, le=200)
    max_comments_per_post: int = Field(10, ge=1, le=200)
    mode: Literal[
        "live",
        "fake_polarized_fictitious",
        "fake_moderate_fictitious",
        "fake_neutral_fictitious",
        "fake_polarized_general",
        "fake_moderate_general",
        "fake_neutral_general",
    ] = "live"
