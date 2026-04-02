from .adapters import GNewsAdapter
from ..registry import register_source

register_source("gnews", GNewsAdapter())
