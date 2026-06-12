"""Provider-agnostic tool-calling agent loop.

Both Anthropic and OpenAI expose function/tool calling but with different wire
formats, so we keep one small loop per provider rather than a leaky abstraction.
A caller supplies provider-agnostic tool specs ({name, description, parameters})
and an async `execute(name, args) -> str` callback; we run the model, dispatch
any tool calls back through `execute`, and feed the results in until the model
produces a final text answer (or we hit MAX_STEPS).
"""
from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable

import httpx

from bot.config import settings

log = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MAX_STEPS = 5  # tool round-trips before we give up
MAX_TOKENS = 1024

Tool = dict
ExecuteFn = Callable[[str, dict], Awaitable[str]]


async def run_agent(
    system: str,
    user_text: str,
    tools: list[Tool],
    execute: ExecuteFn,
    history: list[dict] | None = None,
) -> str | None:
    """Run the configured provider's agent loop. Returns the final text, or None
    if the assistant is disabled / errored / produced no answer.

    `history` is prior conversation as [{role: 'user'|'assistant', content: str}],
    prepended so the model can answer in context."""
    history = history or []
    try:
        if settings.ai_provider == "anthropic":
            return await _run_anthropic(system, user_text, tools, execute, history)
        if settings.ai_provider == "openai":
            return await _run_openai(system, user_text, tools, execute, history)
        if settings.ai_provider == "gemini":
            return await _run_gemini(system, user_text, tools, execute, history)
    except Exception:  # noqa: BLE001 — never crash the bot on an AI failure
        log.exception("AI agent failed")
        return None
    return None


async def _run_anthropic(system, user_text, tools, execute, history) -> str | None:
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    atools = [
        {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
        for t in tools
    ]
    messages: list[dict] = [
        {"role": h["role"], "content": h["content"]} for h in history
    ]
    messages.append({"role": "user", "content": user_text})
    async with httpx.AsyncClient(timeout=60) as http:
        for _ in range(MAX_STEPS):
            body = {
                "model": settings.ai_model_name,
                "max_tokens": MAX_TOKENS,
                "system": system,
                "messages": messages,
                "tools": atools,
            }
            resp = await http.post(ANTHROPIC_URL, headers=headers, json=body)
            resp.raise_for_status()
            content = resp.json().get("content", [])
            tool_uses = [b for b in content if b.get("type") == "tool_use"]
            if not tool_uses:
                return "".join(
                    b.get("text", "") for b in content if b.get("type") == "text"
                ).strip()
            messages.append({"role": "assistant", "content": content})
            results = []
            for tu in tool_uses:
                out = await execute(tu["name"], tu.get("input") or {})
                results.append(
                    {"type": "tool_result", "tool_use_id": tu["id"], "content": out}
                )
            messages.append({"role": "user", "content": results})
    return None


async def _run_openai(system, user_text, tools, execute, history) -> str | None:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "content-type": "application/json",
    }
    otools = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in tools
    ]
    messages: list[dict] = [{"role": "system", "content": system}]
    messages += [{"role": h["role"], "content": h["content"]} for h in history]
    messages.append({"role": "user", "content": user_text})
    async with httpx.AsyncClient(timeout=60) as http:
        for _ in range(MAX_STEPS):
            body = {"model": settings.ai_model_name, "messages": messages, "tools": otools}
            resp = await http.post(OPENAI_URL, headers=headers, json=body)
            resp.raise_for_status()
            msg = resp.json()["choices"][0]["message"]
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                return (msg.get("content") or "").strip()
            messages.append(msg)
            for tc in tool_calls:
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                out = await execute(tc["function"]["name"], args)
                messages.append(
                    {"role": "tool", "tool_call_id": tc["id"], "content": out}
                )
    return None


async def _run_gemini(system, user_text, tools, execute, history) -> str | None:
    headers = {
        "x-goog-api-key": settings.gemini_api_key,
        "content-type": "application/json",
    }
    url = GEMINI_URL.format(model=settings.ai_model_name)
    gtools = [
        {
            "function_declarations": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                }
                for t in tools
            ]
        }
    ]
    contents: list[dict] = [
        {"role": "model" if h["role"] == "assistant" else "user", "parts": [{"text": h["content"]}]}
        for h in history
    ]
    contents.append({"role": "user", "parts": [{"text": user_text}]})
    async with httpx.AsyncClient(timeout=60) as http:
        for _ in range(MAX_STEPS):
            body = {
                "system_instruction": {"parts": [{"text": system}]},
                "contents": contents,
                "tools": gtools,
            }
            resp = await http.post(url, headers=headers, json=body)
            resp.raise_for_status()
            candidates = resp.json().get("candidates", [])
            if not candidates:
                return None
            content = candidates[0].get("content", {}) or {}
            parts = content.get("parts", []) or []
            calls = [p["functionCall"] for p in parts if "functionCall" in p]
            if not calls:
                return "".join(p.get("text", "") for p in parts if "text" in p).strip()
            contents.append(content)  # echo the model turn back
            fr_parts = []
            for call in calls:
                out = await execute(call.get("name", ""), call.get("args") or {})
                fr_parts.append(
                    {
                        "functionResponse": {
                            "name": call.get("name", ""),
                            "response": {"result": out},
                        }
                    }
                )
            contents.append({"role": "user", "parts": fr_parts})
    return None
