"""LLM client with OpenAI primary and optional Gemini fallback.

Adapted from ContentFlow `llm_client.py` for ExposureFlow multi-tenant execution plane.
"""

from __future__ import annotations

import logging

from exposureflow_api.config import settings

logger = logging.getLogger(__name__)


def llm_available() -> bool:
    return bool(settings.openai_api_key or settings.gemini_api_key)


def _writing_model() -> str:
    return settings.llm_writing_model or settings.llm_lite_model or "gpt-4o-mini"


async def achat(
    *,
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.5,
    max_tokens: int | None = None,
) -> str:
    target = model or _writing_model()
    if settings.openai_api_key:
        try:
            return await _call_openai(messages, target, temperature, max_tokens)
        except Exception as exc:
            logger.warning("OpenAI achat failed: %s", exc)
    if settings.gemini_api_key and "gemini" in (target or "").lower():
        return await _call_gemini(messages, target, temperature, max_tokens)
    if settings.gemini_api_key:
        return await _call_gemini(messages, settings.llm_lite_model or "gemini-2.0-flash", temperature, max_tokens)
    raise RuntimeError("No LLM API key configured (OPENAI_API_KEY or GEMINI_API_KEY)")


def chat_sync(
    *,
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.5,
    max_tokens: int | None = None,
) -> str:
    target = model or _writing_model()
    if settings.openai_api_key:
        try:
            return _call_openai_sync(messages, target, temperature, max_tokens)
        except Exception as exc:
            logger.warning("OpenAI chat_sync failed: %s", exc)
    if settings.gemini_api_key:
        return _call_gemini_sync(messages, settings.llm_lite_model or "gemini-2.0-flash", temperature, max_tokens)
    raise RuntimeError("No LLM API key configured (OPENAI_API_KEY or GEMINI_API_KEY)")


async def _call_openai(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int | None,
) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    kwargs: dict = {"model": model, "messages": messages, "temperature": temperature}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    resp = await client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def _call_openai_sync(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int | None,
) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    kwargs: dict = {"model": model, "messages": messages, "temperature": temperature}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    resp = client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


async def _call_gemini(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int | None,
) -> str:
    import httpx

    system = "\n".join(m["content"] for m in messages if m["role"] == "system")
    user_parts = [m["content"] for m in messages if m["role"] != "system"]
    prompt = f"{system}\n\n{chr(10).join(user_parts)}".strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": settings.gemini_api_key or ""}
    body: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    if max_tokens is not None:
        body["generationConfig"]["maxOutputTokens"] = max_tokens
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_gemini_sync(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int | None,
) -> str:
    import httpx

    system = "\n".join(m["content"] for m in messages if m["role"] == "system")
    user_parts = [m["content"] for m in messages if m["role"] != "system"]
    prompt = f"{system}\n\n{chr(10).join(user_parts)}".strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": settings.gemini_api_key or ""}
    body: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    if max_tokens is not None:
        body["generationConfig"]["maxOutputTokens"] = max_tokens
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
