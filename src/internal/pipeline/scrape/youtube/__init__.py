from .adapters import YouTubeAdapter
from ..registry import register_source

register_source("youtube", YouTubeAdapter())
