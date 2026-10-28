from __future__ import annotations

import base64
import os
import random
import time
from pathlib import Path
from typing import Any, Callable

from ..config import VisionConfig
from ..errors import VisionError, VisionUnavailable
from ..models import Usage
from .base import VisionResult


class KelpieVisionBackend:
    """Thin OpenAI Responses client for the discovered Kelpie gateway shape."""

    name = "kelpie"

    def __init__(
        self,
        config: VisionConfig,
        *,
        client: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.model = (
            config.kelpie.model.strip()
            or os.environ.get("KELPIE_MODEL", "").strip()
            or os.environ.get("LLM_VISION_DEPLOYMENT", "").strip()
        )
        self._client = client
        self._sleep = sleep

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        base_url = (
            self.config.kelpie.base_url.strip()
            or os.environ.get("KELPIE_PROXY_BASE_URL", "").strip()
        ).rstrip("/")
        if not base_url or not self.model:
            raise VisionUnavailable(
                "Kelpie proxy and model are not configured; set KELPIE_PROXY_BASE_URL "
                "and KELPIE_MODEL or configure vision.kelpie."
            )
        if not base_url.endswith("/openai/v1"):
            base_url += "/openai/v1"
        try:
            import httpx
            from openai import OpenAI
        except ImportError as exc:
            raise VisionUnavailable("Install doc2md[kelpie] for the Kelpie client.") from exc
        self._client = OpenAI(
            base_url=base_url,
            api_key=os.environ.get("KELPIE_PROXY_API_KEY", "unused"),
            http_client=httpx.Client(timeout=self.config.timeout_s, trust_env=True),
            timeout=self.config.timeout_s,
            max_retries=0,
        )
        return self._client

    @staticmethod
    def _prompt(prompt_id: str) -> str:
        root = Path(__file__).resolve().parents[3]
        prompt_path = root / "prompts" / f"{prompt_id}.txt"
        try:
            return prompt_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError as exc:
            raise VisionError(f"Prompt file not found: {prompt_path}") from exc

    @staticmethod
    def _usage(response: Any, text: str) -> Usage:
        usage = getattr(response, "usage", None)

        def value(*names: str) -> int | None:
            for name in names:
                candidate = getattr(usage, name, None) if usage is not None else None
                if candidate is None and isinstance(usage, dict):
                    candidate = usage.get(name)
                if candidate is not None:
                    return int(candidate)
            return None

        input_tokens = value("input_tokens", "prompt_tokens")
        output_tokens = value("output_tokens", "completion_tokens")
        total_tokens = value("total_tokens")
        if input_tokens is None or output_tokens is None:
            input_tokens = max(1, len(text) // 4) if input_tokens is None else input_tokens
            output_tokens = max(1, len(text) // 4) if output_tokens is None else output_tokens
            return Usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                estimated=True,
            )
        return Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens if total_tokens is not None else input_tokens + output_tokens,
            estimated=False,
        )

    def _call(self, operation: Callable[[], Any]) -> Any:
        for attempt in range(self.config.max_retries + 1):
            try:
                return operation()
            except Exception as exc:
                status = getattr(exc, "status_code", None)
                transient = status == 429 or (isinstance(status, int) and status >= 500)
                transient = transient or type(exc).__name__ in {
                    "APITimeoutError",
                    "APIConnectionError",
                }
                if not transient or attempt >= self.config.max_retries:
                    if type(exc).__name__ in {"APITimeoutError", "APIConnectionError"}:
                        raise VisionUnavailable(f"Kelpie request unavailable: {exc}") from exc
                    raise VisionError(f"Kelpie request failed: {exc}") from exc
                self._sleep(min(2**attempt, 16) + random.random())
        raise VisionError("Kelpie retry loop exhausted")

    def _transcribe(self, image_png: bytes, *, prompt_id: str, max_tokens: int) -> VisionResult:
        prompt = self._prompt(prompt_id)
        encoded = base64.b64encode(image_png).decode("ascii")
        started = time.perf_counter()
        response = self._call(
            lambda: self._get_client().responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{encoded}",
                            },
                        ],
                    }
                ],
                max_output_tokens=max_tokens,
                store=False,
            )
        )
        text = self._response_text(response)
        if not text.strip():
            raise VisionError("Kelpie response returned empty text")
        return VisionResult(
            text=text,
            usage=self._usage(response, text),
            model=self.model,
            latency_s=time.perf_counter() - started,
            request_id=getattr(response, "id", None),
        )

    @staticmethod
    def _response_text(response: Any) -> str:
        direct = str(getattr(response, "output_text", "") or "")
        if direct.strip():
            return direct
        chunks: list[str] = []
        for item in getattr(response, "output", []) or []:
            contents = (
                item.get("content", [])
                if isinstance(item, dict)
                else getattr(item, "content", [])
            )
            for content in contents or []:
                content_type = (
                    content.get("type")
                    if isinstance(content, dict)
                    else getattr(content, "type", None)
                )
                value = (
                    content.get("text")
                    if isinstance(content, dict)
                    else getattr(content, "text", None)
                )
                if value and content_type in {"output_text", "reasoning_text"}:
                    chunks.append(str(value))
        return "\n".join(chunks)

    def describe_image(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult:
        del lang
        return self._transcribe(image_png, prompt_id=prompt_id, max_tokens=self.config.max_tokens)

    def transcribe_page(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult:
        del lang
        return self._transcribe(
            image_png,
            prompt_id=prompt_id,
            max_tokens=self.config.transcribe_max_tokens,
        )
