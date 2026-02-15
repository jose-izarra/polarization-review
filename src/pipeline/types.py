from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


TimeFilter = Literal["day", "week", "month"]
ResultStatus = Literal["ok", "degraded", "error"]
ContentType = Literal["post", "comment"]


@dataclass(slots=True)
class SearchRequest:
    query: str
    time_filter: TimeFilter = "week"
    max_posts: int = 30
    max_comments_per_post: int = 10


@dataclass(slots=True)
class NormalizedItem:
    id: str
    text: str
    url: str
    timestamp: str
    engagement_score: int
    content_type: ContentType


@dataclass(slots=True)
class EvidenceItem:
    id: str
    snippet: str
    url: str


@dataclass(slots=True)
class LLMAssessment:
    polarization_score: float
    confidence: float
    rationale: str
    evidence_ids: list[str]


@dataclass(slots=True)
class PolarizationResult:
    query: str
    collected_at: str
    sample_size: int
    polarization_score: float | None
    confidence: float | None
    rationale: str
    evidence: list[EvidenceItem]
    status: ResultStatus
    error_message: str | None

    def to_dict(self) -> dict:
        return asdict(self)
