from langfuse import Langfuse
from typing import Optional, Tuple

from config import settings
from .logger_service import error_log


# Initialize Langfuse client
langfuse = Langfuse(
    secret_key=settings.LANGFUSE_SECRET_KEY,
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    host=settings.LANGFUSE_HOST
) if settings.LANGFUSE_SECRET_KEY and settings.LANGFUSE_PUBLIC_KEY else None

# # 1. Get prompt from Langfuse
# uncompiled_prompt = langfuse.get_prompt(prompt_name)
# prompt = uncompiled_prompt.compile()

# # 2. Create a trace for this operation
# trace = langfuse.trace(
#     name="privacy_scan",
#     environment=settings.ENVIRONMENT or 'development',
# )


def get_compiled_prompt(prompt_name: str, version: Optional[int] = None) -> Tuple[str, object]:
    """
    Get and compile a prompt from Langfuse.

    Args:
        prompt_name: Name of the prompt stored in Langfuse
        version: Optional version number of the prompt. If None, uses the latest version.

    Returns:
        tuple: (compiled_prompt_string, uncompiled_prompt_object)
        The uncompiled_prompt_object contains metadata like version number.

    Raises:
        Exception: If Langfuse is not configured or prompt cannot be fetched
    """
    if not langfuse:
        error_log(
            action="get_compiled_prompt",
            error="Langfuse not configured. Please set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY in .env",
            prompt_name=prompt_name
        )
        raise ValueError("Langfuse not configured")
    
    try:
        compiled_prompt = langfuse.get_prompt(prompt_name, version=version).compile()
        return compiled_prompt
    except Exception as e:
        error_log(
            action="get_compiled_prompt",
            error=str(e),
            prompt_name=prompt_name,
            version=version
        )
        raise
