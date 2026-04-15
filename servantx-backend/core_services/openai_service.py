import asyncio

from openai import OpenAI, AsyncOpenAI
from typing import Union, Optional
from pydantic import BaseModel

from config import settings
from .logger_service import error_log, info_log, warning_log
from .langfuse_service import get_compiled_prompt


async def _call_with_retry(coro_fn, max_retries=2, base_delay=1.0):
    """Retry an async OpenAI call on transient failures."""
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except Exception as e:
            err_str = str(e).lower()
            # Only retry on transient errors
            if any(t in err_str for t in ("rate limit", "timeout", "503", "502", "529", "overloaded")):
                last_exc = e
                if attempt < max_retries:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
            raise  # Non-transient error — re-raise immediately
    raise last_exc


def chat_with_openai(
    text: str,
    langfuse_prompt: Optional[str] = None,
    prompt: Optional[str] = None,
    model: str = "o4-mini",
    schema: Optional[BaseModel] = None
) -> Union[str, dict]:
    """
    Chat with OpenAI (without Langfuse tracing)

    Args:
        text: The input text to analyze
        langfuse_prompt: Name of the prompt stored in Langfuse (optional)
        prompt: Direct system prompt string (optional)
        model: OpenAI model to use (default: "o4-mini")
        schema: Optional Pydantic schema for structured output. If None, returns plain text.

    Returns:
        If schema is None: plain text string
        If schema is provided: dict with parsed structured response
    """
    if not settings.OPENAI_API_KEY:
        error_log(
            action="openai_chat",
            error="OpenAI API key not configured. Please set OPENAI_API_KEY in .env"
        )
        return "" if schema is None else {}

    system_prompt = ""

    if langfuse_prompt:
        try:
            system_prompt = get_compiled_prompt(langfuse_prompt, version=None)
        except Exception as e:
            error_log(
                action="openai_chat",
                error=f"Failed to get prompt from Langfuse: {str(e)}"
            )
            return "" if schema is None else {}

    elif prompt:
        system_prompt = prompt

    if prompt and langfuse_prompt:
        warning_log(
            action="openai_chat",
            warning="Both prompt and langfuse_prompt provided; using langfuse_prompt.",
            function="chat_with_openai",
            file="core/openai_service",
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        if schema is None:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            output_text = response.choices[0].message.content
            info_log(
                action="openai_chat",
                model=model,
                tokens_used=response.usage.total_tokens if response.usage else 0
            )
            return output_text
        else:
            response = client.responses.parse(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                text_format=schema
            )
            output_dict = (
                response.output_parsed.model_dump()
                if hasattr(response.output_parsed, "model_dump")
                else dict(response.output_parsed)
            )
            info_log(
                action="openai_chat_structured",
                model=model,
                tokens_used=response.usage.total_tokens if response.usage else 0
            )
            return output_dict

    except Exception as e:
        error_log(
            action="openai_chat",
            error=str(e),
            model=model
        )
        return "" if schema is None else {}


async def chat_with_openai_async(
    text: str,
    langfuse_prompt: Optional[str] = None,
    prompt: Optional[str] = None,
    model: str = "o4-mini",
    schema: Optional[BaseModel] = None
) -> Union[str, dict]:
    """
    Async version: Chat with OpenAI (without Langfuse tracing)

    Args:
        text: The input text to analyze
        langfuse_prompt: Name of the prompt stored in Langfuse (optional)
        prompt: Direct system prompt string (optional)
        model: OpenAI model to use (default: "o4-mini")
        schema: Optional Pydantic schema for structured output. If None, returns plain text.

    Returns:
        If schema is None: plain text string
        If schema is provided: dict with parsed structured response
    """
    if not settings.OPENAI_API_KEY:
        error_log(
            action="openai_chat_async",
            error="OpenAI API key not configured. Please set OPENAI_API_KEY in .env"
        )
        return "" if schema is None else {}

    system_prompt = ""

    if langfuse_prompt:
        try:
            system_prompt = get_compiled_prompt(langfuse_prompt, version=None)
        except Exception as e:
            error_log(
                action="openai_chat_async",
                error=f"Failed to get prompt from Langfuse: {str(e)}"
            )
            return "" if schema is None else {}

    elif prompt:
        system_prompt = prompt

    if prompt and langfuse_prompt:
        warning_log(
            action="openai_chat_async",
            warning="Both prompt and langfuse_prompt provided; using langfuse_prompt.",
            function="chat_with_openai_async",
            file="core/openai_service",
        )

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        if schema is None:
            response = await _call_with_retry(lambda: client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            ))
            output_text = response.choices[0].message.content
            info_log(
                action="openai_chat_async",
                model=model,
                tokens_used=response.usage.total_tokens if response.usage else 0
            )
            return output_text
        else:
            response = await _call_with_retry(lambda: client.responses.parse(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                text_format=schema
            ))
            output_dict = (
                response.output_parsed.model_dump()
                if hasattr(response.output_parsed, "model_dump")
                else dict(response.output_parsed)
            )
            info_log(
                action="openai_chat_async_structured",
                model=model,
                tokens_used=response.usage.total_tokens if response.usage else 0
            )
            return output_dict

    except Exception as e:
        error_log(
            action="openai_chat_async",
            error=str(e),
            model=model
        )
        return "" if schema is None else {}
