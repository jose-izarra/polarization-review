"""
Reddit Data Collection Module for Polarization Analysis

Collects posts and comments from Reddit for a given search term,
normalizes them into a structured format for downstream stance detection
and sentiment analysis.

Environment Variables Required:
    REDDIT_CLIENT_ID: Reddit app client ID
    REDDIT_CLIENT_SECRET: Reddit app client secret
    REDDIT_USER_AGENT: Custom user agent string (optional, has default)
"""

import logging
from datetime import datetime, timezone

import praw
import prawcore
from src.internal.config import config as app_config

from .utils import (
    DEFAULT_CONFIG,
    _count_subreddits,
    _extract_top_subreddits,
    _passes_quality,
)

logger = logging.getLogger(__name__)


def init_reddit_client():
    """
    Initialize the Reddit client using environment variables.

    Returns:
        praw.Reddit: Authenticated Reddit client in read-only mode.

    Raises:
        EnvironmentError: If required credentials are missing.
        prawcore.exceptions.ResponseException: If credentials are invalid.
    """
    client_id = app_config.reddit_client_id
    client_secret = app_config.reddit_client_secret
    user_agent = app_config.reddit_user_agent

    if not client_id:
        raise EnvironmentError(
            "REDDIT_CLIENT_ID environment variable is required. "
            "Get it from https://www.reddit.com/prefs/apps"
        )
    if not client_secret:
        raise EnvironmentError(
            "REDDIT_CLIENT_SECRET environment variable is required. "
            "Get it from https://www.reddit.com/prefs/apps"
        )

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        ratelimit_seconds=300,  # Wait up to 5 minutes if rate limited
    )

    # Verify connection works (will raise if credentials are invalid)
    if not reddit.read_only:
        # Force read-only mode for safety
        reddit.read_only = True

    return reddit


def discover_subreddits(
    reddit,
    query: str,
    limit: int = 10,
    min_subscribers: int = 10_000,
) -> list[str]:
    """
    Phase 1 discovery: search Reddit communities relevant to the query,
    filtered by subscriber count to exclude dead subreddits.

    Uses reddit.subreddits.search() which searches by subreddit title and
    description (equivalent to Reddit's community search UI).

    Always includes "all" as the first entry regardless of results.

    Args:
        reddit: Authenticated praw.Reddit instance.
        query: The search term to find relevant subreddits for.
        limit: Maximum results from subreddits.search(). Pass 0 to skip.
        min_subscribers: Minimum subscriber count to include a subreddit.

    Returns:
        List of subreddit display_names, always starting with "all".
    """
    if limit <= 0:
        return ["all"]

    discovered = ["all"]
    try:
        for sub in reddit.subreddits.search(query, limit=limit):
            # Accessing sub attributes (subscribers, display_name) triggers a
            # live API fetch per subreddit — wrap each in its own try/except
            # because quarantined subs raise 403, banned subs raise 404.
            try:
                if sub.subscribers and sub.subscribers >= min_subscribers:
                    name = sub.display_name
                    if name.lower() != "all" and name not in discovered:
                        discovered.append(name)
            except Exception as e:
                logger.warning("Could not read metadata for discovered sub: %s", e)
                continue
    except prawcore.exceptions.RequestException as e:
        logger.warning("Subreddit discovery failed, falling back to r/all only: %s", e)
    except Exception as e:
        logger.warning("Unexpected error during subreddit discovery: %s", e)

    return discovered


def fetch_posts(
    reddit,
    search_term,
    subreddit_name="all",
    limit=100,
    sort="relevance",
    time_filter="month",
):
    """
    Search a subreddit for posts matching the search term.

    Args:
        reddit: Authenticated praw.Reddit instance.
        search_term: The topic to search for.
        subreddit_name: Name of the subreddit to search. Use "all" for all of Reddit.
        limit: Maximum number of posts to return (max 250 in practice).
        sort: How to sort results — "relevance", "top", "new", "comments".
        time_filter: Time window — "hour", "day", "week", "month", "year", "all".

    Returns:
        List of dicts in the unified output schema.
    """
    subreddit = reddit.subreddit(subreddit_name)
    posts = []

    try:
        for submission in subreddit.search(
            search_term, sort=sort, time_filter=time_filter, limit=limit
        ):
            # Build the text field: title always included, selftext only for self posts
            if submission.is_self and submission.selftext:
                text = f"{submission.title}\n\n{submission.selftext}"
            else:
                text = submission.title

            # Skip deleted/removed posts
            if text.strip() in ("[deleted]", "[removed]", ""):
                continue

            posts.append(
                {
                    "id": f"reddit_post_{submission.id}",
                    "source": "reddit",
                    "platform_id": submission.id,
                    "search_term": search_term,
                    "text": text,
                    "author": str(submission.author)
                    if submission.author
                    else "[deleted]",
                    "timestamp": datetime.fromtimestamp(
                        submission.created_utc, tz=timezone.utc
                    ).isoformat(),
                    "url": f"https://reddit.com{submission.permalink}",
                    "engagement": {
                        "likes": submission.score,
                        "replies": submission.num_comments,
                        "shares": 0,
                        "score": submission.score,
                    },
                    "metadata": {
                        "subreddit": submission.subreddit.display_name,
                        "content_type": "post",
                        "parent_id": None,
                        "is_self_post": submission.is_self,
                        "link_url": submission.url if not submission.is_self else None,
                        "flair": submission.link_flair_text,
                    },
                }
            )

    except prawcore.exceptions.Redirect:
        logger.warning("Subreddit r/%s does not exist, skipping", subreddit_name)
    except prawcore.exceptions.NotFound:
        logger.warning("Subreddit r/%s not found, skipping", subreddit_name)
    except prawcore.exceptions.Forbidden:
        logger.warning("Subreddit r/%s is private, skipping", subreddit_name)
    except prawcore.exceptions.RequestException as e:
        logger.warning("Network error searching r/%s: %s", subreddit_name, e)
    except Exception as e:
        logger.warning("Failed to search r/%s: %s", subreddit_name, e)

    return posts


def fetch_comments(reddit, submission_id, search_term, max_comments=100):
    """
    Fetch comments from a specific Reddit post.

    Args:
        reddit: Authenticated praw.Reddit instance.
        submission_id: The Reddit ID of the post (e.g., "abc123").
        search_term: The original search term (for tagging).
        max_comments: Maximum number of comments to collect from this post.

    Returns:
        List of dicts in the unified output schema.
    """
    try:
        submission = reddit.submission(id=submission_id)

        # replace_more(limit=0) removes all "load more comments" stubs
        # without making extra API calls
        submission.comments.replace_more(limit=0)

        comments = []
        for comment in submission.comments.list():
            if len(comments) >= max_comments:
                break

            # Skip deleted/removed comments
            if not hasattr(comment, "body") or comment.body in (
                "[deleted]",
                "[removed]",
                "",
            ):
                continue

            # Count direct replies
            reply_count = 0
            if hasattr(comment, "replies"):
                reply_count = len(comment.replies)

            comments.append(
                {
                    "id": f"reddit_comment_{comment.id}",
                    "source": "reddit",
                    "platform_id": comment.id,
                    "search_term": search_term,
                    "text": comment.body,
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "timestamp": datetime.fromtimestamp(
                        comment.created_utc, tz=timezone.utc
                    ).isoformat(),
                    "url": f"https://reddit.com{comment.permalink}",
                    "engagement": {
                        "likes": comment.score,
                        "replies": reply_count,
                        "shares": 0,
                        "score": comment.score,
                    },
                    "metadata": {
                        "subreddit": comment.subreddit.display_name,
                        "content_type": "comment",
                        "parent_id": comment.parent_id,
                        "is_self_post": None,
                        "link_url": None,
                        "flair": getattr(comment, "author_flair_text", None),
                    },
                }
            )

        return comments

    except prawcore.exceptions.RequestException as e:
        logger.warning("Network error fetching comments for %s: %s", submission_id, e)
        return []
    except Exception as e:
        logger.warning("Failed to fetch comments for %s: %s", submission_id, e)
        return []


def collect_reddit_data(search_term, scrape_config=None, reddit=None):
    """
    Main entry point. Collects posts and comments from Reddit for the given search term.

    Uses a two-phase dynamic subreddit discovery strategy:
      Phase 1 — reddit.subreddits.search() finds topic-relevant communities.
      Phase 2 — top subreddits from r/all results are re-queried for more depth.

    Args:
        search_term: The topic to analyze.
        scrape_config: Optional dict to override default settings.
        reddit: Optional pre-initialized Reddit client. If None, will initialize one.

    Returns:
        Dict containing all collected data, organized by type, with a summary.

    Raises:
        EnvironmentError: If credentials are missing and no reddit client provided.
    """
    cfg = {**DEFAULT_CONFIG, **(scrape_config or {})}

    if reddit is None:
        reddit = init_reddit_client()

    all_posts = []
    all_comments = []

    # --- Phase 1: Discover relevant subreddits via PRAW community search ---
    logger.info('Discovering subreddits for: "%s"', search_term)
    discovered_subs = discover_subreddits(
        reddit,
        search_term,
        limit=cfg["subreddit_discovery_limit"],
        min_subscribers=cfg["min_subscribers"],
    )
    # "all" is always first; slice it off since we handle r/all separately below
    phase1_subs = [s for s in discovered_subs if s.lower() != "all"]
    logger.info("Phase 1 discovered: %s", phase1_subs or "(none beyond r/all)")

    # --- Fetch r/all first so Phase 2 can bootstrap from those results ---
    logger.info('Searching Reddit for: "%s"', search_term)
    all_posts_from_all = []
    for sort in cfg["sorts"]:
        limit = cfg["posts_per_subreddit_all"]
        logger.debug("Searching r/all (sort=%s, limit=%d)", sort, limit)
        posts = fetch_posts(
            reddit,
            search_term,
            subreddit_name="all",
            limit=limit,
            sort=sort,
            time_filter=cfg["time_filter"],
        )
        all_posts_from_all.extend(posts)
    all_posts.extend(all_posts_from_all)

    # --- Phase 2: Extract top subreddits from r/all results ---
    phase2_subs = _extract_top_subreddits(
        all_posts_from_all,
        top_n=cfg["phase2_top_n"],
        exclude={"all"},
    )
    logger.info("Phase 2 bootstrapped: %s", phase2_subs or "(no results from r/all)")

    # --- Merge Phase 1 + Phase 2, deduplicated, excluding "all" (done above) ---
    combined_subs = list(dict.fromkeys(phase1_subs + phase2_subs))
    logger.info("Combined subreddits to query: %s", combined_subs or "(none)")

    # --- Fetch each discovered subreddit ---
    for subreddit_name in combined_subs:
        limit = cfg["posts_per_subreddit"]
        for sort in cfg["sorts"]:
            logger.debug(
                "Searching r/%s (sort=%s, limit=%d)", subreddit_name, sort, limit
            )
            posts = fetch_posts(
                reddit,
                search_term,
                subreddit_name=subreddit_name,
                limit=limit,
                sort=sort,
                time_filter=cfg["time_filter"],
            )
            all_posts.extend(posts)

    # Deduplicate posts (same post can appear across r/all and specific subreddits)
    seen_ids = set()
    unique_posts = []
    for post in all_posts:
        if post["platform_id"] not in seen_ids:
            seen_ids.add(post["platform_id"])
            unique_posts.append(post)
    all_posts = unique_posts

    logger.info("Found %d unique posts", len(all_posts))

    # --- Collect comments from top posts ---
    ranked_posts = sorted(
        all_posts, key=lambda p: p["engagement"]["score"], reverse=True
    )
    top_posts = ranked_posts[: cfg["top_posts_for_comments"]]

    logger.info("Fetching comments from top %d posts", len(top_posts))

    for i, post in enumerate(top_posts):
        logger.debug(
            "[%d/%d] r/%s — score: %d",
            i + 1,
            len(top_posts),
            post["metadata"]["subreddit"],
            post["engagement"]["score"],
        )
        comments = fetch_comments(
            reddit,
            post["platform_id"],
            search_term,
            max_comments=cfg["comments_per_post"],
        )
        all_comments.extend(comments)

    logger.info("Collected %d comments", len(all_comments))

    # --- Apply quality filters ---
    all_posts = [p for p in all_posts if _passes_quality(p, cfg["min_text_length"])]
    all_comments = [
        c for c in all_comments if _passes_quality(c, cfg["min_text_length"])
    ]

    # --- Build result ---
    subreddits_searched = ["all"] + combined_subs
    result = {
        "search_term": search_term,
        "collected_at": datetime.now(tz=timezone.utc).isoformat(),
        "config_used": cfg,
        "data": {"posts": all_posts, "comments": all_comments},
        "summary": {
            "total_posts": len(all_posts),
            "total_comments": len(all_comments),
            "total_items": len(all_posts) + len(all_comments),
            "subreddits_searched": subreddits_searched,
            "subreddits_found": list(
                set(p["metadata"]["subreddit"] for p in all_posts)
            ),
            "top_subreddits_by_volume": _count_subreddits(all_posts + all_comments),
        },
    }

    logger.info(
        "Done. Total: %d items (%d posts + %d comments)",
        result["summary"]["total_items"],
        result["summary"]["total_posts"],
        result["summary"]["total_comments"],
    )

    return result
