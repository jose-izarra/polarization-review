from .adapters import RedditAdapter
from ..registry import register_source

register_source("reddit", RedditAdapter())
