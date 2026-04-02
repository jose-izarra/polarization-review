from ..registry import register_source
from .adapters import YouTubeAdapter

register_source("youtube", YouTubeAdapter())
