from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a text response."""

    @abstractmethod
    def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: type[ModelT]
    ) -> ModelT:
        """Generate and validate structured output."""

