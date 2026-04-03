from src.internal.pipeline.llm.sources.registry import register
from src.internal.pipeline.llm.sources.youtube.calls import YouTubeLLMProcessor

register(YouTubeLLMProcessor())
