from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ..vision.base import VisionBackend


@dataclass(frozen=True)
class JudgeParseResult:
    scores: dict[str, int]
    error: str | None = None


def parse_judge_response(text: str) -> JudgeParseResult:
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    else:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start < 0 or end <= start:
            return JudgeParseResult({}, "judge response contained no JSON object")
        candidate = candidate[start : end + 1]
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return JudgeParseResult({}, f"invalid judge JSON: {exc.msg}")
    if not isinstance(payload, dict):
        return JudgeParseResult({}, "judge JSON must be an object")
    scores = payload.get("scores", payload)
    if not isinstance(scores, dict):
        return JudgeParseResult({}, "judge scores must be an object")
    parsed: dict[str, int] = {}
    for key, value in scores.items():
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2:
            return JudgeParseResult({}, f"invalid score for {key}")
        parsed[str(key)] = value
    return JudgeParseResult(parsed)


class JudgeClient:
    def __init__(self, backend: VisionBackend) -> None:
        self.backend = backend

    def judge(self, image_png: bytes, *, prompt_id: str = "judge.v1") -> JudgeParseResult:
        try:
            result = self.backend.transcribe_page(image_png, prompt_id=prompt_id)
        except Exception as exc:
            return JudgeParseResult({}, f"judge call failed: {type(exc).__name__}: {exc}")
        return parse_judge_response(result.text)
