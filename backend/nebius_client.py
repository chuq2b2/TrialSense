import json
import re

import requests

from config import NEBIUS_API_KEY, NEBIUS_BASE_URL, NEBIUS_MODEL


class NebiusError(Exception):
    pass


def _extract_json(text: str) -> dict | list:
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise NebiusError("Nebius returned invalid JSON.") from exc


def chat_completion(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.1,
) -> str:
    if not NEBIUS_API_KEY:
        raise NebiusError(
            "NEBIUS_API_KEY is not configured. Add it to backend/.env."
        )

    url = f"{NEBIUS_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": model or NEBIUS_MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {NEBIUS_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=90,
        )
    except requests.RequestException as exc:
        raise NebiusError(f"Nebius request failed: {exc}") from exc

    if response.status_code >= 400:
        raise NebiusError(
            f"Nebius API error ({response.status_code}): {response.text[:500]}"
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise NebiusError("Unexpected Nebius response format.") from exc


def chat_json(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.1,
) -> dict | list:
    content = chat_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        temperature=temperature,
    )
    return _extract_json(content)
