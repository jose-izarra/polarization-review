from __future__ import annotations

from typing import Callable


def call_llm(
    system_prompt: str,
    user_payload: str,
    *,
    model: str | None = None,
    timeout_seconds: int = 45,
    _override: Callable[[str, str], str] | None = None,
) -> str:
    """Single entry point for all LLM calls in the pipeline.

    _override is for test injection only. In production it is always None.
    Falls back to mock_call_model when GEMINI_API_KEY is not set.
    """
    if _override is not None:
        return _override(system_prompt, user_payload)

    from src.internal.config import config

    if config.gemini_api_key is None:
        from src.internal.pipeline.llm.mock_llm import mock_call_model

        return mock_call_model(system_prompt, user_payload)

    chosen_model = model or config.polarization_model
    return _call_gemini(
        system_prompt, user_payload, model=chosen_model, timeout_seconds=timeout_seconds
    )


def _call_gemini(
    system_prompt: str,
    user_payload: str,
    model: str,
    timeout_seconds: int,
) -> str:
    """Internal Gemini API wrapper. Not part of the public interface."""
    from google import genai
    from google.genai import types

    from src.internal.config import config

    client = genai.Client(api_key=config.gemini_api_key)
    try:
        response = client.models.generate_content(
            model=model,
            contents=user_payload,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini API error: {exc}") from exc
    return response.text
