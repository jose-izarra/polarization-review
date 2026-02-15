from __future__ import annotations

import json
import os
import re
from urllib import error, request

from .types import LLMAssessment, NormalizedItem


_DEFAULT_MODEL = "gpt-4o-mini"
_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def _truncate(text: str, limit: int = 280) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _build_user_payload(query: str, items: list[NormalizedItem]) -> str:
    avg_score = round(sum(i.engagement_score for i in items) / max(len(items), 1), 2)
    evidence = [
        {
            "id": item.id,
            "score": item.engagement_score,
            "type": item.content_type,
            "text": _truncate(item.text),
        }
        for item in items
    ]
    payload = {
        "query": query,
        "stats": {
            "sample_size": len(items),
            "avg_engagement_score": avg_score,
        },
        "evidence": evidence,
    }
    return json.dumps(payload, ensure_ascii=True)


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = _JSON_BLOCK_RE.search(text)
    if not match:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(match.group(0))


def _validate_assessment(data: dict) -> LLMAssessment:
    required = {"polarization_score", "confidence", "rationale", "evidence_ids"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"Missing keys: {sorted(missing)}")

    score = float(data["polarization_score"])
    confidence = float(data["confidence"])
    rationale = str(data["rationale"]).strip()
    evidence_ids_raw = data["evidence_ids"]

    if not 0 <= score <= 100:
        raise ValueError("polarization_score out of bounds")
    if not 0 <= confidence <= 1:
        raise ValueError("confidence out of bounds")
    if not rationale:
        raise ValueError("rationale cannot be empty")
    if not isinstance(evidence_ids_raw, list):
        raise ValueError("evidence_ids must be a list")

    evidence_ids = [str(x) for x in evidence_ids_raw if str(x).strip()]

    return LLMAssessment(
        polarization_score=score,
        confidence=confidence,
        rationale=rationale,
        evidence_ids=evidence_ids,
    )


def _call_openai_chat(system_prompt: str, user_payload: str, model: str, timeout_seconds: int) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for LLM assessment")

    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": model,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ],
    }

    req = request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error: {exc.code} {details}") from exc

    try:
        return raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Unexpected OpenAI response format") from exc


def assess_polarization(
    query: str,
    items: list[NormalizedItem],
    model: str | None = None,
    timeout_seconds: int = 45,
    call_model=None,
) -> LLMAssessment:
    """
    Assess polarization from one batch model call.

    call_model(system_prompt, user_payload) can be injected for tests.
    """
    if not items:
        raise ValueError("Cannot assess polarization with zero items")

    chosen_model = model or os.environ.get("POLARIZATION_MODEL", _DEFAULT_MODEL)

    system_prompt = (
        "You are evaluating political polarization for a topic using ONLY provided evidence. "
        "Return JSON with keys: polarization_score (0-100), confidence (0-1), rationale, evidence_ids. "
        "Lower confidence when data is sparse or one-sided. No extra keys."
    )
    user_payload = _build_user_payload(query, items)

    invoke = call_model or (
        lambda sys_prompt, user_input: _call_openai_chat(
            sys_prompt, user_input, model=chosen_model, timeout_seconds=timeout_seconds
        )
    )

    raw_response = invoke(system_prompt, user_payload)
    try:
        parsed = _extract_json(raw_response)
        return _validate_assessment(parsed)
    except Exception:
        retry_prompt = system_prompt + " Return only one valid JSON object and nothing else."
        retry_response = invoke(retry_prompt, user_payload)
        parsed = _extract_json(retry_response)
        return _validate_assessment(parsed)
