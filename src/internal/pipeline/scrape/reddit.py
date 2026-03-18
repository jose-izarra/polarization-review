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

import json
import os
from datetime import datetime, timezone

import praw
import prawcore
from src.internal.config.config import config as app_config

# Priority subreddits for political polarization analysis
PRIORITY_SUBREDDITS = [
    "all",  # Catch-all: search everything
    "politics",  # US-centric political news and discussion
    "worldnews",  # International news
    "news",  # General news
    "PoliticalDiscussion",  # More civil, policy-focused discussion
    "Conservative",  # Right-leaning US politics
    "Liberal",  # Left-leaning US politics
    "neutralpolitics",  # Requires sourced claims, less polarized
]

# Default configuration for data collection
DEFAULT_CONFIG = {
    "subreddits": PRIORITY_SUBREDDITS,
    "posts_per_subreddit": 50,
    "posts_per_subreddit_all": 100,  # Higher limit for r/all
    "sorts": ["relevance", "top"],
    "time_filter": "month",
    "top_posts_for_comments": 20,  # Fetch comments for top N posts
    "comments_per_post": 100,
    "min_text_length": 20,  # Discard items shorter than this
}


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
        print(f"[WARNING] Subreddit r/{subreddit_name} does not exist, skipping.")
    except prawcore.exceptions.NotFound:
        print(f"[WARNING] Subreddit r/{subreddit_name} not found, skipping.")
    except prawcore.exceptions.Forbidden:
        print(f"[WARNING] Subreddit r/{subreddit_name} is private, skipping.")
    except prawcore.exceptions.RequestException as e:
        print(f"[WARNING] Network error searching r/{subreddit_name}: {e}")
    except Exception as e:
        print(f"[WARNING] Failed to search r/{subreddit_name}: {e}")

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
        print(f"[WARNING] Network error fetching comments for {submission_id}: {e}")
        return []
    except Exception as e:
        print(f"[WARNING] Failed to fetch comments for {submission_id}: {e}")
        return []


def _count_subreddits(items):
    """Helper: count how many items came from each subreddit."""
    counts = {}
    for item in items:
        sub = item["metadata"]["subreddit"]
        counts[sub] = counts.get(sub, 0) + 1
    # Return sorted by count descending
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def _passes_quality(item, min_text_length):
    """Helper: check if an item passes quality filters."""
    # Minimum text length
    if len(item["text"].strip()) < min_text_length:
        return False
    # Skip deleted content
    if item["text"].strip() in ("[deleted]", "[removed]"):
        return False
    return True


def collect_reddit_data(search_term, scrape_config=None, reddit=None):
    """
    Main entry point. Collects posts and comments from Reddit for the given search term.

    Args:
        search_term: The topic to analyze.
        scrape_config: Optional dict to override default settings.
        reddit: Optional pre-initialized Reddit client. If None, will initialize one.

    Returns:
        Dict containing all collected data, organized by type, with a summary.

    Raises:
        EnvironmentError: If credentials are missing and no reddit client provided.
    """
    # Merge configuration
    cfg = {**DEFAULT_CONFIG, **(scrape_config or {})}

    # Initialize Reddit client if not provided
    if reddit is None:
        reddit = init_reddit_client()

    all_posts = []
    all_comments = []

    # --- Collect posts ---
    print(f'Searching Reddit for: "{search_term}"')

    for subreddit_name in cfg["subreddits"]:
        limit = (
            cfg["posts_per_subreddit_all"]
            if subreddit_name == "all"
            else cfg["posts_per_subreddit"]
        )

        for sort in cfg["sorts"]:
            print(f"  Searching r/{subreddit_name} (sort={sort}, limit={limit})...")
            posts = fetch_posts(
                reddit,
                search_term,
                subreddit_name=subreddit_name,
                limit=limit,
                sort=sort,
                time_filter=cfg["time_filter"],
            )
            all_posts.extend(posts)

    # Deduplicate posts (same post can appear in r/all and in a specific subreddit)
    seen_ids = set()
    unique_posts = []
    for post in all_posts:
        if post["platform_id"] not in seen_ids:
            seen_ids.add(post["platform_id"])
            unique_posts.append(post)
    all_posts = unique_posts

    print(f"  Found {len(all_posts)} unique posts")

    # --- Collect comments from top posts ---
    # Sort posts by engagement (score) to prioritize the most-discussed ones
    ranked_posts = sorted(
        all_posts, key=lambda p: p["engagement"]["score"], reverse=True
    )
    top_posts = ranked_posts[: cfg["top_posts_for_comments"]]

    print(f"Fetching comments from top {len(top_posts)} posts...")

    for i, post in enumerate(top_posts):
        print(
            f"  [{i + 1}/{len(top_posts)}] r/{post['metadata']['subreddit']} "
            f"— score: {post['engagement']['score']}"
        )
        comments = fetch_comments(
            reddit,
            post["platform_id"],
            search_term,
            max_comments=cfg["comments_per_post"],
        )
        all_comments.extend(comments)

    print(f"  Collected {len(all_comments)} comments")

    # --- Apply quality filters ---
    all_posts = [p for p in all_posts if _passes_quality(p, cfg["min_text_length"])]
    all_comments = [
        c for c in all_comments if _passes_quality(c, cfg["min_text_length"])
    ]

    # --- Build result ---
    result = {
        "search_term": search_term,
        "collected_at": datetime.now(tz=timezone.utc).isoformat(),
        "config_used": cfg,
        "data": {"posts": all_posts, "comments": all_comments},
        "summary": {
            "total_posts": len(all_posts),
            "total_comments": len(all_comments),
            "total_items": len(all_posts) + len(all_comments),
            "subreddits_searched": cfg["subreddits"],
            "subreddits_found": list(
                set(p["metadata"]["subreddit"] for p in all_posts)
            ),
            "top_subreddits_by_volume": _count_subreddits(all_posts + all_comments),
        },
    }

    print(
        f"\nDone. Total: {result['summary']['total_items']} items "
        f"({result['summary']['total_posts']} posts + "
        f"{result['summary']['total_comments']} comments)"
    )

    return result


def save_results(result, filename=None, output_dir=None):
    """
    Save collection results to a JSON file.

    Args:
        result: The collection result dict from collect_reddit_data.
        filename: Optional filename. If None, generates from search term and timestamp.
        output_dir: Optional directory to save to. Defaults to current directory.

    Returns:
        str: Path to the saved file.
    """
    if filename is None:
        # Generate filename from search term and timestamp
        safe_term = result["search_term"].replace(" ", "_").lower()[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_{safe_term}_{timestamp}.json"

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
    else:
        filepath = filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Saved to {filepath}")
    return filepath


# Quick test configuration (< 2 minutes)
QUICK_CONFIG = {
    "subreddits": ["all"],
    "posts_per_subreddit_all": 25,
    "sorts": ["relevance"],
    "top_posts_for_comments": 5,
    "comments_per_post": 20,
}

# Thorough analysis configuration (10-15 minutes)
THOROUGH_CONFIG = {
    "subreddits": PRIORITY_SUBREDDITS,
    "posts_per_subreddit": 100,
    "posts_per_subreddit_all": 200,
    "sorts": ["relevance", "top", "new"],
    "time_filter": "year",
    "top_posts_for_comments": 50,
    "comments_per_post": 200,
}

# Historical analysis configuration
HISTORICAL_CONFIG = {
    "time_filter": "all",  # No time restriction
    "sorts": ["top"],  # Only the most upvoted content survives long-term
}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <search_term> [--quick|--thorough|--historical]")
        print("\nExamples:")
        print('  python main.py "immigration policy"')
        print('  python main.py "Israel Palestine" --quick')
        print('  python main.py "climate change" --thorough')
        sys.exit(1)

    search_term = sys.argv[1]

    # Determine config based on flags
    scrape_config = None
    if "--quick" in sys.argv:
        scrape_config = QUICK_CONFIG
        print("Using quick configuration")
    elif "--thorough" in sys.argv:
        scrape_config = THOROUGH_CONFIG
        print("Using thorough configuration")
    elif "--historical" in sys.argv:
        scrape_config = HISTORICAL_CONFIG
        print("Using historical configuration")

    try:
        result = collect_reddit_data(search_term, scrape_config=scrape_config)
        save_results(result)
    except EnvironmentError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
