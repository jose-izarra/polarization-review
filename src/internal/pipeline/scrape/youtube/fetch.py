"""
YouTube Data Collection Module for Polarization Analysis

Collects videos and comments from YouTube for a given search term,
returning them in the unified raw item format consumed by normalize_raw_item().

Environment Variables Required:
    YOUTUBE_API_KEY: YouTube Data API v3 key
"""

from __future__ import annotations

import logfire
from src.internal.config import config as app_config

from .utils import DEFAULT_CONFIG


def _build_youtube_client(api_key: str):
    from googleapiclient.discovery import build

    return build("youtube", "v3", developerKey=api_key)


def _fetch_transcript(video_id: str) -> str | None:
    """Fetch transcript for a YouTube video. Returns None on failure."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript = YouTubeTranscriptApi().fetch(video_id)
        full_text = " ".join(snippet.text for snippet in transcript)
        return full_text
    except Exception as exc:
        logfire.debug("Could not fetch transcript", video_id=video_id, error=str(exc))
        return None


def _search_videos(
    youtube,
    query: str,
    max_videos: int,
    order: str,
    page_token: str | None = None,
    exclude_ids: set[str] | None = None,
) -> tuple[list[dict], str | None]:
    """Search for videos and return (video_list, next_page_token).

    Args:
        page_token: YouTube pagination token for fetching subsequent pages.
        exclude_ids: Video IDs already collected; matching results are skipped.
    """
    params: dict = dict(
        q=query,
        type="video",
        part="snippet",
        order=order,
        maxResults=max_videos,
    )
    if page_token:
        params["pageToken"] = page_token

    response = youtube.search().list(**params).execute()
    next_page_token: str | None = response.get("nextPageToken")

    exclude_ids = exclude_ids or set()
    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        if video_id in exclude_ids:
            continue

        snippet = item["snippet"]
        title = snippet.get("title", "")
        description = snippet.get("description", "")
        published_at = snippet.get("publishedAt", "")

        text = f"{title}. {description}"[:500]
        transcript = _fetch_transcript(video_id)

        videos.append(
            {
                "platform_id": f"youtube_video_{video_id}",
                "source": "youtube",
                "text": text,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "timestamp": published_at,
                "engagement": {"score": 0},
                "metadata": {
                    "content_type": "post",
                    "transcript": transcript,
                },
                "_video_id": video_id,
            }
        )

    return videos, next_page_token


def _fetch_comments(youtube, video_id: str, max_comments: int) -> list[dict]:
    try:
        response = (
            youtube.commentThreads()
            .list(
                videoId=video_id,
                part="snippet",
                order="relevance",
                textFormat="plainText",
                maxResults=max_comments,
            )
            .execute()
        )
    except Exception as exc:
        if getattr(exc, "status_code", None) == 403:
            logfire.warning("Comments disabled for video, skipping", video_id=video_id)
            return []
        raise

    comments = []
    for item in response.get("items", []):
        top = item["snippet"]["topLevelComment"]
        comment_id = top["id"]
        snippet = top["snippet"]
        comments.append(
            {
                "platform_id": f"youtube_comment_{comment_id}",
                "source": "youtube",
                "text": snippet.get("textDisplay", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}&lcdId={comment_id}",
                "timestamp": snippet.get("publishedAt", ""),
                "engagement": {"score": snippet.get("likeCount", 0)},
                "metadata": {
                    "content_type": "comment",
                    "parent_video_id": video_id,
                },
            }
        )

    return comments


def collect_youtube_data(
    query: str,
    config: dict | None = None,
    queries: list[str] | None = None,
) -> dict:
    """Collect YouTube videos and comments for the given query.

    If *queries* is provided (a list of search strings), all queries are searched
    and their video results are merged and deduplicated before comments are fetched.
    This is used to surface videos from multiple perspectives (for/against/neutral).

    After exhausting all provided queries, if fewer than *min_videos_with_comments*
    videos have comments enabled, additional pages are fetched from the first query
    until the minimum is met or there are no more pages.

    Returns:
        {"data": {"posts": [...], "comments": [...]}}
    """
    if not app_config.youtube_api_key:
        raise RuntimeError("YOUTUBE_API_KEY is required for YouTube scraping")
    api_key = app_config.youtube_api_key

    cfg = {**DEFAULT_CONFIG, **(config or {})}
    min_with_comments: int = cfg["min_videos_with_comments"]
    youtube = _build_youtube_client(api_key)

    search_queries = queries if queries else [query]

    posts: list[dict] = []
    comments: list[dict] = []
    seen_ids: set[str] = set()
    videos_with_comments: int = 0

    # Phase 1: search across all provided queries, merge + dedup
    first_query_next_page: str | None = None
    for i, q in enumerate(search_queries):
        batch, next_page = _search_videos(
            youtube, q, cfg["max_videos"], cfg["order"], exclude_ids=seen_ids
        )
        for video in batch:
            video_id = video.pop("_video_id")
            seen_ids.add(video_id)
            posts.append(video)
            video_comments = _fetch_comments(
                youtube, video_id, cfg["max_comments_per_video"]
            )
            if video_comments:
                videos_with_comments += 1
            comments.extend(video_comments)
        if i == 0:
            first_query_next_page = next_page

    # Phase 2: if still below minimum, page through additional results from query 1
    page_token = first_query_next_page
    while videos_with_comments < min_with_comments and page_token:
        batch, page_token = _search_videos(
            youtube,
            query,
            cfg["max_videos"],
            cfg["order"],
            page_token=page_token,
            exclude_ids=seen_ids,
        )
        if not batch:
            break
        for video in batch:
            video_id = video.pop("_video_id")
            seen_ids.add(video_id)
            posts.append(video)
            video_comments = _fetch_comments(
                youtube, video_id, cfg["max_comments_per_video"]
            )
            if video_comments:
                videos_with_comments += 1
            comments.extend(video_comments)

    return {"data": {"posts": posts, "comments": comments}}
