"""
YouTube Data Collection Module for Polarization Analysis

Collects videos and comments from YouTube for a given search term,
returning them in the unified raw item format consumed by normalize_raw_item().

Environment Variables Required:
    YOUTUBE_API_KEY: YouTube Data API v3 key
"""

from __future__ import annotations

import logging

from src.internal.config.config import config as app_config

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "max_videos": 10,
    "max_comments_per_video": 20,
    "order": "relevance",
}


def _build_youtube_client(api_key: str):
    from googleapiclient.discovery import build

    return build("youtube", "v3", developerKey=api_key)


def _fetch_transcript(video_id: str) -> str | None:
    """Fetch and truncate transcript for a YouTube video. Returns None on failure."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join(entry["text"] for entry in transcript_list)
        return full_text[:2000]
    except Exception as exc:
        logger.debug("Could not fetch transcript for %s: %s", video_id, exc)
        return None


def _search_videos(youtube, query: str, max_videos: int, order: str) -> list[dict]:
    response = (
        youtube.search()
        .list(
            q=query,
            type="video",
            part="snippet",
            order=order,
            maxResults=max_videos,
        )
        .execute()
    )

    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
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

    return videos


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
            logger.warning("Comments disabled for video %s, skipping.", video_id)
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


def collect_youtube_data(query: str, config: dict | None = None) -> dict:
    """Collect YouTube videos and comments for the given query.

    Returns:
        {"data": {"posts": [...], "comments": [...]}}
    """
    if not app_config.youtube_api_key:
        raise RuntimeError("YOUTUBE_API_KEY is required for YouTube scraping")
    api_key = app_config.youtube_api_key

    cfg = {**DEFAULT_CONFIG, **(config or {})}
    youtube = _build_youtube_client(api_key)

    video_items = _search_videos(youtube, query, cfg["max_videos"], cfg["order"])

    posts = []
    comments = []

    for video in video_items:
        video_id = video.pop("_video_id")
        posts.append(video)
        video_comments = _fetch_comments(
            youtube, video_id, cfg["max_comments_per_video"]
        )
        comments.extend(video_comments)

    return {"data": {"posts": posts, "comments": comments}}
