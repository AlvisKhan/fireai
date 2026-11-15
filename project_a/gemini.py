"""JSON-only Gemini transport for the assignment's model experiments."""

import json
import os
import re
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Reply:
    value: dict
    usage: dict
    model: str


def generate(prompt: str, schema: dict) -> Reply:
    key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "")
    if not key or not re.fullmatch(r"gemini-[a-zA-Z0-9._-]+", model):
        raise RuntimeError("Set GEMINI_API_KEY and GEMINI_MODEL for your Gemini free-tier project.")
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
            },
        }).encode(),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"Gemini returned HTTP {error.code}") from None
    candidates = payload.get("candidates", [])
    if not candidates or candidates[0].get("finishReason") != "STOP":
        raise RuntimeError("Gemini did not return a complete response.")
    parts = candidates[0]["content"]["parts"]
    value = json.loads("".join(p.get("text", "") for p in parts if not p.get("thought")))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    return Reply(value, payload.get("usageMetadata", {}), payload.get("modelVersion", model))
