# servantx-backend/core_services/anthropic_service.py
"""
Anthropic Claude API client.
Supports prompt caching: pass cache_system=True to cache the system prompt block.
Returns (result, usage_dict) so callers can log tokens.
"""
import asyncio
import time
from typing import Optional, Union

import anthropic
from pydantic import BaseModel

from config import settings
from .logger_service import error_log, info_log


async def _claude_with_retry(coro_fn, max_retries: int = 2, base_delay: float = 1.0):
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except Exception as e:
            err_str = str(e).lower()
            if any(t in err_str for t in ("rate_limit", "overloaded", "529", "503", "timeout")):
                last_exc = e
                if attempt < max_retries:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
            raise
    raise last_exc


async def chat_with_claude_async(
    text: str,
    prompt: str,
    model: str = "claude-sonnet-4-6",
    cache_system: bool = False,
    schema: Optional[type] = None,
) -> tuple[Union[str, dict], dict]:
    """
    Call Claude. Returns (result, usage).

    Args:
        text: user message content
        prompt: system prompt
        model: Claude model ID
        cache_system: if True, marks the system prompt with cache_control for prompt caching
        schema: optional Pydantic model — if provided, wraps prompt to request JSON and parses output

    Returns:
        (result, usage) where usage = {
            "input_tokens": int,
            "output_tokens": int,
            "cache_read_tokens": int,
            "cache_write_tokens": int,
        }
    """
    empty = {} if schema else ""

    if not settings.ANTHROPIC_API_KEY:
        error_log(action="claude_async", error="ANTHROPIC_API_KEY not set")
        return empty, {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0}

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    system_block: list = []
    if cache_system:
        system_block = [{"type": "text", "text": prompt, "cache_control": {"type": "ephemeral"}}]
    else:
        system_block = [{"type": "text", "text": prompt}]

    user_content = text
    if schema:
        user_content = (
            text
            + "\n\nRespond with ONLY a valid JSON object matching this schema: "
            + str(schema.model_json_schema())
            + ". No markdown, no explanation."
        )

    try:
        t0 = time.monotonic()
        response = await _claude_with_retry(lambda: client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_block,
            messages=[{"role": "user", "content": user_content}],
        ))
        latency_ms = int((time.monotonic() - t0) * 1000)

        usage = response.usage
        usage_dict = {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            "cache_write_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
            "latency_ms": latency_ms,
        }

        raw = response.content[0].text if response.content else ""

        info_log(
            action="claude_async",
            model=model,
            tokens_used=usage.input_tokens + usage.output_tokens,
            cache_hit=usage_dict["cache_read_tokens"] > 0,
        )

        if schema:
            import json, re
            # Strip markdown code fences if present
            clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
            try:
                return schema(**json.loads(clean)).model_dump(), usage_dict
            except Exception as parse_err:
                error_log(action="claude_async_parse", error=str(parse_err), raw=raw[:200])
                return {}, usage_dict

        return raw, usage_dict

    except Exception as e:
        error_log(action="claude_async", error=str(e), model=model)
        return empty, {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0, "latency_ms": None}
