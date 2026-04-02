from ..registry import register_source
from .adapters import RedditAdapter

register_source("reddit", RedditAdapter())
