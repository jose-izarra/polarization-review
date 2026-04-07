DEFAULT_CONFIG = {
    "max_videos": 20,
    "max_comments_per_video": 30,
    "order": "relevance",
    # Minimum number of videos that must have comments enabled. If fewer are
    # found in the first batch, additional pages are fetched automatically.
    # Defaults to max_videos at runtime (see collect_youtube_data).
    "min_videos_with_comments": 10,
}
