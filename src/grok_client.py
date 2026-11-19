"""Groq API client module for StreamIQ.

Provides a secure, high-performance integration with Groq's OpenAI-compatible API.
Configured for official endpoint https://api.groq.com/openai/v1 and model llama-3.3-70b-versatile.
"""

from __future__ import annotations

import os
from typing import Any, Generator

# Attempt optional python-dotenv loading for local .env files
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Attempt optional Streamlit import to read from st.secrets if running inside Streamlit
try:
    import streamlit as st

    _STREAMLIT_AVAILABLE = True
except ImportError:
    _STREAMLIT_AVAILABLE = False

# Official Groq OpenAI-compatible API configuration
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL: str = "llama-3.3-70b-versatile"

# Backward-compatibility alias constants
XAI_BASE_URL: str = GROQ_BASE_URL
DEFAULT_GROK_MODEL: str = DEFAULT_GROQ_MODEL


def get_groq_api_key(explicit_key: str | None = None) -> str | None:
    """Retrieve the Groq API key from secure configuration sources.

    Evaluation order:
    1. Explicitly passed parameter (e.g., from a secure UI password input widget)
    2. Streamlit secrets (`st.secrets["GROQ_API_KEY"]` or `st.secrets.get("GROQ_API_KEY")`)
    3. Environment variable `GROQ_API_KEY` (including values loaded from .env)

    Returns:
        The API key string if found, or None. Note: The key is never logged or printed.
    """
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    # Check Streamlit secrets if available
    if _STREAMLIT_AVAILABLE:
        try:
            if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                secret_val = st.secrets["GROQ_API_KEY"]
                if secret_val and str(secret_val).strip():
                    return str(secret_val).strip()
        except Exception:
            # st.secrets might raise FileNotFoundError if secrets.toml is absent
            pass

    # Check system environment variables (including those loaded from .env)
    env_key = os.getenv("GROQ_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    return None


# Backward-compatibility alias
get_xai_api_key = get_groq_api_key


def get_grok_client(api_key: str | None = None) -> Any:
    """Initialize and return an OpenAI SDK client configured for Groq's endpoint.

    Args:
        api_key: Optional explicit API key. If omitted, resolved via `get_groq_api_key()`.

    Returns:
        Configured `OpenAI` client instance pointing to `https://api.groq.com/openai/v1`.

    Raises:
        ImportError: If the `openai` package is not installed.
        ValueError: If no valid Groq API key could be located.
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "The 'openai' package is required to communicate with the Groq API. "
            "Please install it using 'pip install openai'."
        ) from exc

    resolved_key = get_groq_api_key(api_key)
    if not resolved_key:
        raise ValueError(
            "Groq API key not found. Please set 'GROQ_API_KEY' in your environment, "
            ".env file, or in .streamlit/secrets.toml."
        )

    return OpenAI(api_key=resolved_key, base_url=GROQ_BASE_URL)


# Alias for clean Groq naming
get_groq_client = get_grok_client


def test_grok_connection(
    api_key: str | None = None,
    model: str = DEFAULT_GROQ_MODEL,
) -> dict[str, Any]:
    """Execute a lightweight connectivity and authentication test against the Groq API.

    Args:
        api_key: Optional explicit Groq API key.
        model: Model identifier to verify (default: 'llama-3.3-70b-versatile').

    Returns:
        A dictionary containing:
        - success: bool
        - model: str
        - message: str (response text on success, or user-friendly error explanation)
        - error_type: str | None
    """
    try:
        client = get_grok_client(api_key=api_key)
    except (ImportError, ValueError) as err:
        return {
            "success": False,
            "model": model,
            "message": str(err),
            "error_type": err.__class__.__name__,
        }

    try:
        import openai

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a connectivity test assistant for StreamIQ. Reply with 'OK'.",
                },
                {"role": "user", "content": "Ping test."},
            ],
            max_tokens=10,
            temperature=0.0,
        )
        content = (response.choices[0].message.content or "").strip()
        return {
            "success": True,
            "model": model,
            "message": content or "Connection successful.",
            "error_type": None,
        }

    except openai.AuthenticationError:
        return {
            "success": False,
            "model": model,
            "message": "Authentication failed: The provided Groq API key (GROQ_API_KEY) is invalid or inactive.",
            "error_type": "AuthenticationError",
        }
    except openai.RateLimitError:
        return {
            "success": False,
            "model": model,
            "message": "Rate limit exceeded: Groq API request quota or tokens-per-minute (TPM) limit reached.",
            "error_type": "RateLimitError",
        }
    except (openai.APIConnectionError, openai.APITimeoutError):
        return {
            "success": False,
            "model": model,
            "message": f"Network connection failed: Unable to connect to Groq endpoint at {GROQ_BASE_URL}.",
            "error_type": "ConnectionError",
        }
    except openai.BadRequestError as err:
        return {
            "success": False,
            "model": model,
            "message": f"Bad request to Groq API ({err.message if hasattr(err, 'message') else str(err)}).",
            "error_type": "BadRequestError",
        }
    except openai.APIError as err:
        return {
            "success": False,
            "model": model,
            "message": f"Groq API service error: {str(err)}",
            "error_type": "APIError",
        }
    except Exception as err:
        return {
            "success": False,
            "model": model,
            "message": f"Unexpected error during connection test: {str(err)}",
            "error_type": err.__class__.__name__,
        }


# Alias for clean Groq naming
test_groq_connection = test_grok_connection


def query_grok(
    prompt: str,
    system_prompt: str | None = None,
    api_key: str | None = None,
    model: str = DEFAULT_GROQ_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 1500,
) -> str:
    """Send a prompt to Groq and return the completion response text.

    Args:
        prompt: User question or instruction.
        system_prompt: Optional system role context and grounding instructions.
        api_key: Optional explicit API key.
        model: Model identifier (default: 'llama-3.3-70b-versatile').
        temperature: Sampling temperature (default: 0.2 for analytical precision).
        max_tokens: Maximum tokens to generate.

    Returns:
        The response content string.
    """
    client = get_grok_client(api_key=api_key)

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (response.choices[0].message.content or "").strip()


# Alias for clean Groq naming
query_groq = query_grok


def stream_grok(
    prompt: str,
    system_prompt: str | None = None,
    api_key: str | None = None,
    model: str = DEFAULT_GROQ_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 2000,
) -> Generator[str, None, None]:
    """Stream response tokens from Groq for real-time UI display.

    Yields:
        Individual string tokens as they arrive from the Groq API stream.
    """
    client = get_grok_client(api_key=api_key)

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


# Alias for clean Groq naming
stream_groq = stream_grok


if __name__ == "__main__":
    print(f"StreamIQ Groq AI Client [Target Endpoint: {GROQ_BASE_URL}]")
    print(f"Target Model: {DEFAULT_GROQ_MODEL}")

    key_present = get_groq_api_key() is not None
    print(f"API Key Detected: {'[YES - Configured (GROQ_API_KEY)]' if key_present else '[NO - Missing/Unset (GROQ_API_KEY)]'}")

    print("\nRunning connection verification test...")
    result = test_groq_connection()
    if result["success"]:
        print(f"SUCCESS: Groq responded: '{result['message']}'")
    else:
        print(f"NOTICE: {result['error_type']} - {result['message']}")
