import os
from typing import Any, Dict, List, Optional

try:
    import openai
    from openai import OpenAI

    HAS_OPENAI_V1 = True
except (ImportError, AttributeError):
    try:
        import openai

        HAS_OPENAI_V1 = False
    except ImportError:
        openai = None
        HAS_OPENAI_V1 = False


def openai_chat_create(
    model: str,
    messages: List[Dict[str, str]],
    api_key: Optional[str] = None,
    temperature: float = 0.8,
    max_tokens: int = 4096,
    seed: Optional[int] = None,
    **kwargs: Any,
) -> str:
    """
    Wrapper for OpenAI ChatCompletion.create to handle both v0 and v1+ SDKs.
    """
    if openai is None:
        raise ImportError("openai package not installed. Please run: pip install openai")

    # Use provided API key or environment variable
    effective_api_key = api_key or os.environ.get("OPENAI_API_KEY")

    if HAS_OPENAI_V1:
        # Use v1+ client pattern
        client = OpenAI(api_key=effective_api_key)

        # Merge kwargs to allow additional parameters if needed
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed,
            **kwargs,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        response = client.chat.completions.create(**params)
        return response.choices[0].message.content
    else:
        # Legacy v0.x pattern
        if effective_api_key:
            openai.api_key = effective_api_key

        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        if seed is not None:
            params["seed"] = seed

        # Filter None values just in case
        params = {k: v for k, v in params.items() if v is not None}

        response = openai.ChatCompletion.create(**params)
        return response.choices[0].message.content
