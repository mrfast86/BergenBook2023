"""
Scorecard Analysis — OpenRouter (free vision models)

Uses OpenAI-compatible API via OpenRouter with free Llama 3.2 Vision.

Requires OPENROUTER_API_KEY in .streamlit/secrets.toml or as an env var.
Get a free key at: https://openrouter.ai
"""
import base64
import json
import os
import re

_PROMPT = """You are analyzing a photo of a golf scorecard. Extract every player's hole-by-hole stroke scores.

Return ONLY a valid JSON object — no markdown, no explanation, just the JSON:

{
  "players": ["Name1", "Name2"],
  "scores": [
    [4, 5, 3, 4, 4, 5, 3, 4, 4, 5, 4, 3, 4, 4, 5, 3, 4, 4],
    [5, 4, 4, 5, 3, 4, 4, 5, 4, 4, 3, 4, 5, 4, 4, 5, 3, 5]
  ],
  "holes": 18
}

Rules:
- scores[i] is the list of hole-by-hole strokes for players[i]
- Each stroke value is an integer between 1 and 15
- holes is 9 or 18 depending on the round
- Include up to 4 players
- Skip par, yardage, handicap, and total rows — only player stroke rows
- If a name is unclear write "Player 1", "Player 2", etc.
- Return ONLY the JSON object
"""

_MODEL = "google/gemma-3-27b-it:free"


def _get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            pass
    return key


def _detect_media_type(image_bytes: bytes) -> str:
    if image_bytes[:2] == b"\xff\xd8":
        return "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def extract_scorecard(image_bytes: bytes) -> dict:
    result = {
        "players":       [],
        "scores":        [],
        "holes":         18,
        "ocr_available": True,
        "raw_text":      "",
        "debug_rows":    [],
        "error":         None,
    }

    api_key = _get_api_key()
    if not api_key:
        result["error"] = "no_api_key: add OPENROUTER_API_KEY to .streamlit/secrets.toml"
        return result

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        media_type = _detect_media_type(image_bytes)
        b64 = base64.standard_b64encode(image_bytes).decode()
        data_url = f"data:{media_type};base64,{b64}"

        response = client.chat.completions.create(
            model=_MODEL,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": _PROMPT},
                ],
            }],
        )

        content = response.choices[0].message.content
        if not content:
            result["error"] = "empty_response: model returned no content — it may not support vision"
            return result
        raw = content.strip()
        result["raw_text"] = raw

        # Strip markdown fences if the model wrapped it
        clean = re.sub(r"^```[a-z]*\n?", "", raw)
        clean = re.sub(r"\n?```$", "", clean).strip()

        data = json.loads(clean)

        players = data.get("players", [])
        scores  = data.get("scores", [])
        holes   = int(data.get("holes", 18))

        cleaned = []
        for row in scores[:4]:
            cleaned.append([max(1, min(15, int(s))) for s in row[:holes]])

        while len(players) < len(cleaned):
            players.append(f"Player {len(players) + 1}")

        result["players"] = players[:len(cleaned)]
        result["scores"]  = cleaned
        result["holes"]   = holes

    except json.JSONDecodeError as exc:
        result["error"] = f"parse_error: model returned non-JSON — {exc}"
    except Exception as exc:
        result["error"] = f"ai_error: {exc}"

    return result
