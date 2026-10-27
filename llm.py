"""Nebius Token Factory client (OpenAI-compatible API)."""
import os
import time

import openai
from openai import OpenAI

_client = None


class Reply(str):
    """Model text plus optional call metadata."""
    usage = None
    finish_reason = None


def max_tokens() -> int:
    try:
        return int(os.environ.get("MAX_TOKENS", "4096"))
    except ValueError:
        return 4096


REQUIRED_ENV = ("TOKEN_FACTORY_BASE_URL", "TOKEN_FACTORY_API_KEY", "PLANNER_MODEL", "FIXER_MODEL")


class ConfigError(RuntimeError):
    """Required configuration is missing. Never retried."""


class LLMError(RuntimeError):
    """A Token Factory call failed; `status` is the HTTP status when there was one."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def missing_config() -> list[str]:
    return [k for k in REQUIRED_ENV if not os.environ.get(k, "").strip()]


def check_config():
    missing = missing_config()
    if missing:
        raise ConfigError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and restart the server.")


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=os.environ["TOKEN_FACTORY_BASE_URL"].strip(),
            api_key=os.environ["TOKEN_FACTORY_API_KEY"].strip(),
        )
    return _client


def _retryable(e: Exception) -> bool:
    if isinstance(e, openai.APIStatusError):
        return e.status_code in (408, 429) or e.status_code >= 500
    return isinstance(e, openai.APIConnectionError)  # includes timeouts


def ask(model: str, system: str, user: str, retries: int = 2) -> str:
    check_config()
    client = _get_client()
    last = None
    for attempt in range(retries + 1):
        try:
            r = client.chat.completions.create(
                model=model,
                temperature=0.2,
                max_tokens=max_tokens(),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            out = Reply(r.choices[0].message.content or "")
            out.finish_reason = r.choices[0].finish_reason
            u = getattr(r, "usage", None)
            if u is not None:
                out.usage = {"prompt_tokens": u.prompt_tokens,
                             "completion_tokens": u.completion_tokens,
                             "total_tokens": u.total_tokens}
            return out
        except Exception as e:
            status = getattr(e, "status_code", None)
            detail = f"HTTP {status}: {e}" if status else f"{type(e).__name__}: {e}"
            if not _retryable(e):
                raise LLMError(f"Token Factory call failed (not retried) - {detail}", status) from e
            last = (e, detail, status)
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise LLMError(f"Token Factory call failed after {retries + 1} attempts - {last[1]}", last[2]) from last[0]
