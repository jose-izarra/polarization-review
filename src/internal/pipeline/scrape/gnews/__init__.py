from ..registry import register_source
from .adapters import GNewsAdapter

register_source("gnews", GNewsAdapter())
