from __future__ import annotations

import logfire
import sys
from typing import Callable


def _log_api_error(provider: str, model: str, exc: Exception) -> None:
    """Log an API error via logfire (scrubbing-safe) and always print to stderr."""
    logfire.error("LLM API call failed", provider=provider, model=model)
    print(f"[LLM ERROR] {provider} ({model}): {exc}", file=sys.stderr, flush=True)


def _detect_provider(model: str) -> str:
    """Infer provider from model name prefix."""
    m = model.lower()
    if m.startswith(("gpt-", "o1", "o3", "o4")):
        return "gpt"
    if m.startswith("qwen"):
        return "qwen"
    if m.startswith(("mistral", "codestral", "ministral")):
        return "mistral"
    if m.startswith("deepseek"):
        return "deepseek"
    return "gemini"


def call_llm(
    system_prompt: str,
    user_payload: str,
    *,
    model: str | None = None,
    _override: Callable[[str, str], str] | None = None,
) -> str:
    """Single entry point for all LLM calls in the pipeline.

    _override is for test injection only. In production it is always None.
    Falls back to mock_call_model when the relevant API key is not set.
    """
    if _override is not None:
        return _override(system_prompt, user_payload)

    from src.internal.config import config

    chosen_model = model or config.polarization_model
    provider = _detect_provider(chosen_model)

    if provider == "gpt":
        if config.openai_api_key is None:
            logfire.warning(
                "OPENAI_API_KEY not set — falling back to mock responses",
                model=chosen_model,
            )
            from src.internal.pipeline.mock.llm import mock_call_model
            return mock_call_model(system_prompt, user_payload)
        return _call_gpt(system_prompt, user_payload, model=chosen_model)

    if provider == "qwen":
        if config.qwen_api_key is None:
            logfire.warning(
                "QWEN_API_KEY not set — falling back to mock responses",
                model=chosen_model,
            )
            from src.internal.pipeline.mock.llm import mock_call_model
            return mock_call_model(system_prompt, user_payload)
        return _call_qwen(system_prompt, user_payload, model=chosen_model)

    if provider == "mistral":
        if config.mistral_api_key is None:
            logfire.warning(
                "MISTRAL_API_KEY not set — falling back to mock responses",
                model=chosen_model,
            )
            from src.internal.pipeline.mock.llm import mock_call_model
            return mock_call_model(system_prompt, user_payload)
        return _call_mistral(system_prompt, user_payload, model=chosen_model)

    if provider == "deepseek":
        if config.deepseek_api_key is None:
            logfire.warning(
                "DEEPSEEK_API_KEY not set — falling back to mock responses",
                model=chosen_model,
            )
            from src.internal.pipeline.mock.llm import mock_call_model
            return mock_call_model(system_prompt, user_payload)
        return _call_deepseek(system_prompt, user_payload, model=chosen_model)

    # default to gemini
    if config.gemini_api_key is None:
        logfire.warning(
            "GEMINI_API_KEY not set — falling back to mock responses",
            model=chosen_model,
        )
        from src.internal.pipeline.mock.llm import mock_call_model
        return mock_call_model(system_prompt, user_payload)
    return _call_gemini(system_prompt, user_payload, model=chosen_model)


def _call_gemini(
    system_prompt: str,
    user_payload: str,
    model: str,
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
        _log_api_error("Gemini", model, exc)
        raise RuntimeError(f"Gemini API error ({model}): {exc}") from exc
    return response.text


def _call_gpt(
    system_prompt: str,
    user_payload: str,
    model: str,
) -> str:
    """OpenAI GPT wrapper (gpt-4o, gpt-4o-mini, o1, o3, etc.).

    Does NOT pass response_format — the system prompts already ask for a JSON
    array, and using json_object mode would force GPT to return a JSON object
    instead, breaking _extract_json_array in assess.py.

    o1/o3/o4 reasoning models also do not support the temperature parameter,
    so it is skipped for those model families.
    """
    from openai import OpenAI
    from src.internal.config import config

    client = OpenAI(api_key=config.openai_api_key)

    # o1/o3/o4 reasoning models do not support temperature
    _reasoning_model = model.lower().startswith(("o1", "o3", "o4"))
    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ],
    }
    if not _reasoning_model:
        kwargs["temperature"] = 0.0

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        logfire.error("OpenAI API call failed", model=model, error=str(exc))
        raise RuntimeError(f"OpenAI API error ({model}): {exc}") from exc
    return response.choices[0].message.content


def _call_qwen(
    system_prompt: str,
    user_payload: str,
    model: str,
) -> str:
    """Alibaba Qwen wrapper via DashScope OpenAI-compatible endpoint.

    Recommended models: qwen-plus, qwen-turbo, qwen-max.
    Set POLARIZATION_MODEL=qwen-plus (or similar) to use.
    """
    from openai import OpenAI
    from src.internal.config import config

    client = OpenAI(
        api_key=config.qwen_api_key,
        base_url=config.qwen_base_url,
    )
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
        )
    except Exception as exc:
        _log_api_error("Qwen", model, exc)
        raise RuntimeError(f"Qwen API error ({model}): {exc}") from exc
    return response.choices[0].message.content


def _call_mistral(
    system_prompt: str,
    user_payload: str,
    model: str,
) -> str:
    """Mistral AI wrapper.

    Recommended models: mistral-small-latest, mistral-medium-latest,
    mistral-large-latest.
    Set POLARIZATION_MODEL=mistral-small-latest (or similar) to use.
    """
    from mistralai.client import Mistral
    from src.internal.config import config

    client = Mistral(api_key=config.mistral_api_key)
    try:
        response = client.chat.complete(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
        )
    except Exception as exc:
        _log_api_error("Mistral", model, exc)
        raise RuntimeError(f"Mistral API error ({model}): {exc}") from exc
    return response.choices[0].message.content


def _call_deepseek(
    system_prompt: str,
    user_payload: str,
    model: str,
) -> str:
    """DeepSeek wrapper via its OpenAI-compatible endpoint.

    Recommended models: deepseek-chat, deepseek-reasoner.
    Set POLARIZATION_MODEL=deepseek-chat (or similar) to use.
    """
    from openai import OpenAI
    from src.internal.config import config

    client = OpenAI(
        api_key=config.deepseek_api_key,
        base_url="https://api.deepseek.com",
    )
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
        )
    except Exception as exc:
        logfire.error("DeepSeek API call failed", model=model, error=str(exc))
        raise RuntimeError(f"DeepSeek API error ({model}): {exc}") from exc
    return response.choices[0].message.content
