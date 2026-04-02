DEFAULT_CONFIG = {
    # Dynamic discovery controls
    # How many results to pull from subreddits.search()
    "subreddit_discovery_limit": 10,
    "min_subscribers": 10_000,  # Filter out dead/tiny communities
    "phase2_top_n": 5,  # Top subreddits from r/all results to re-query
    # Scraping parameters
    "posts_per_subreddit": 50,
    "posts_per_subreddit_all": 100,  # Higher limit for r/all
    "sorts": ["relevance", "top"],
    "time_filter": "month",
    "top_posts_for_comments": 20,  # Fetch comments for top N posts
    "comments_per_post": 100,
    "min_text_length": 20,  # Discard items shorter than this
}

# Quick test configuration (< 2 minutes) — skips discovery, r/all only
QUICK_CONFIG = {
    "subreddit_discovery_limit": 0,  # Skip Phase 1
    "phase2_top_n": 0,  # Skip Phase 2
    "posts_per_subreddit_all": 25,
    "sorts": ["relevance"],
    "top_posts_for_comments": 5,
    "comments_per_post": 20,
}

# Thorough analysis configuration (10-15 minutes)
THOROUGH_CONFIG = {
    "subreddit_discovery_limit": 20,
    "min_subscribers": 5_000,  # Accept smaller communities
    "phase2_top_n": 10,
    "posts_per_subreddit": 100,
    "posts_per_subreddit_all": 200,
    "sorts": ["relevance", "top", "new"],
    "time_filter": "year",
    "top_posts_for_comments": 50,
    "comments_per_post": 200,
}

# Historical analysis configuration
HISTORICAL_CONFIG = {
    "time_filter": "all",
    "sorts": ["top"],
    # Inherits discovery defaults from DEFAULT_CONFIG
}


def _count_subreddits(items):
    """Helper: count how many items came from each subreddit."""
    counts = {}
    for item in items:
        sub = item["metadata"]["subreddit"]
        counts[sub] = counts.get(sub, 0) + 1
    # Return sorted by count descending
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def _extract_top_subreddits(
    posts: list[dict],
    top_n: int = 5,
    exclude: set[str] | None = None,
) -> list[str]:
    """
    Phase 2: from already-fetched posts, identify the subreddits that appear
    most frequently. Used to bootstrap deeper queries from r/all results.

    Args:
        posts: List of post dicts from fetch_posts() (typically r/all results).
        top_n: How many top subreddits to return.
        exclude: Subreddit names to skip (e.g. {"all"} to avoid re-querying it).

    Returns:
        Up to top_n subreddit display_names ordered by post volume.
    """
    _exclude = {s.lower() for s in (exclude or set())}
    counts = _count_subreddits(posts)
    result = []
    for name in counts:
        if name.lower() not in _exclude and len(result) < top_n:
            result.append(name)
    return result


def _passes_quality(item, min_text_length):
    """Helper: check if an item passes quality filters."""
    # Minimum text length
    if len(item["text"].strip()) < min_text_length:
        return False
    # Skip deleted content
    if item["text"].strip() in ("[deleted]", "[removed]"):
        return False
    return True
