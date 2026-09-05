from __future__ import annotations

import json
from typing import Any

import httpx

from app.llm.base import LLMProvider, ModelT


class OllamaError(RuntimeError):
    pass


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 600.0,
        num_ctx: int = 8192,
        num_predict: int = 1024,
        think: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.num_predict = num_predict
        self.think = think

    def _chat(self, system_prompt: str, user_prompt: str, fmt: Any = None) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "think": self.think,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": 0.1,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            },
        }
        if fmt is not None:
            payload["format"] = fmt
        try:
            response = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
            response.raise_for_status()
            return str(response.json()["message"]["content"])
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise OllamaError(
                f"Unable to use Ollama model '{self.model}' at {self.base_url}: {exc}"
            ) from exc

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return self._chat(system_prompt, user_prompt)

    def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: type[ModelT]
    ) -> ModelT:
        content = self._chat(system_prompt, user_prompt, schema.model_json_schema())
        try:
            return schema.model_validate_json(content)
        except ValueError as exc:
            start, end = content.find("{"), content.rfind("}")
            if start < 0 or end <= start:
                raise OllamaError("Ollama returned malformed structured output") from exc
            return schema.model_validate(json.loads(content[start : end + 1]))

    def health(self) -> dict[str, Any]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = [item.get("name", "") for item in response.json().get("models", [])]
            requested = self.model if ":" in self.model else f"{self.model}:latest"
            available = requested in models
            return {"reachable": True, "model_available": available, "models": models}
        except httpx.HTTPError as exc:
            return {"reachable": False, "model_available": False, "error": str(exc)}
