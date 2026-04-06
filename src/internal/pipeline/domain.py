from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

TimeFilter = Literal["day", "week", "month"]
ResultStatus = Literal["ok", "degraded", "error"]
ContentType = Literal["post", "comment"]


@dataclass(slots=True)
class SearchRequest:
    query: str
    time_filter: TimeFilter = "month"
    max_posts: int = 30
    max_comments_per_post: int = 30
    mode: str = "live"


@dataclass(slots=True)
class NormalizedItem:
    id: str
    text: str
    url: str
    timestamp: str
    engagement_score: int
    content_type: ContentType
    platform: str = "unknown"
    source_lean: str | None = None
    relevance_score: float | None = None
    parent_video_stance: int | None = None
    parent_video_id: str | None = None


@dataclass(slots=True)
class EvidenceItem:
    id: str
    snippet: str
    url: str
    stance: int | None = None
    animosity: int | None = None
    sentiment: int | None = None
    rationale: str | None = None
    source_lean: str | None = None
    platform: str | None = None


@dataclass(slots=True)
class ItemScore:
    id: str
    sentiment: int  # 1-10  (LLM rating)
    stance: int  # -1 (against) / 0 (neutral) / 1 (for)
    animosity: int  # 1-5  (emotional weight)
    r: float  # computed r_i = stance * (sentiment + α*animosity)
    reason: str = ""


@dataclass(slots=True)
class LLMAssessment:
    polarization_score: float
    rationale: str
    evidence_ids: list[str]


@dataclass(slots=True)
class PolarizationResult:
    query: str
    collected_at: str
    sample_size: int
    polarization_score: float | None
    rationale: str
    evidence: list[EvidenceItem]
    status: ResultStatus
    error_message: str | None
    stance_distribution: dict | None = None
    source_breakdown: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)
