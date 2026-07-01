"""
Thin wrapper around the Portkey gateway for calling Claude.

Every agent in this project calls Claude through this single function, which means:
  - one place to change models / add retries / add logging
  - Portkey handles the actual Anthropic API key (never stored in this repo)
  - every call is automatically observable in the Portkey dashboard

Portkey exposes an OpenAI/Anthropic-compatible REST endpoint. We call it directly
with `requests` to keep the dependency footprint small (no extra SDK required).
"""
import json
import re
import requests

from config import config




class PortkeyError(RuntimeError):
    pass


def call_claude(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.2,
    expect_json: bool = False,
) -> str:
    """
    Calls Claude via the Portkey gateway and returns the raw text response.

    If expect_json=True, strips markdown code fences and validates the result
    parses as JSON before returning it (raises PortkeyError if it doesn't).
    """
    config.validate()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.PORTKEY_API_KEY}",
        "x-portkey-virtual-key": config.PORTKEY_VIRTUAL_KEY,
    }

    payload = {
        "model": config.ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        resp = requests.post(config.PORTKEY_BASE_URL, headers=headers, json=payload, timeout=180)
        resp.raise_for_status()
    except requests.Timeout:
        # One retry on timeout — enterprise gateways can occasionally be slow on a single call.
        try:
            resp = requests.post(config.PORTKEY_BASE_URL, headers=headers, json=payload, timeout=180)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise PortkeyError(f"Portkey request failed after retry: {e}") from e
    except requests.RequestException as e:
        raise PortkeyError(f"Portkey request failed: {e}") from e

    data = resp.json()

    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise PortkeyError(f"Unexpected Portkey response shape: {data}") from e

    if expect_json:
        text = _strip_json_fences(text)
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            raise PortkeyError(f"Agent did not return valid JSON: {text[:300]}") from e

    return text


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()
