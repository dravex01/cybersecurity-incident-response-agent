from __future__ import annotations

import hashlib
import math
import re
import threading
from functools import lru_cache
from typing import Protocol


@lru_cache(maxsize=4096)
def _hash_embed(text: str, dimensions: int) -> tuple[float, ...]:
    vector = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "little") % dimensions
        sign = 1 if digest[4] % 2 else -1
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return tuple(value / norm for value in vector)


class EmbeddingFunction(Protocol):
    def __call__(self, input: list[str]) -> list[list[float]]: ...

    def name(self) -> str: ...

    def embed_query(self, input: list[str]) -> list[list[float]]: ...

    def embed_documents(self, input: list[str]) -> list[list[float]]: ...

    def get_config(self) -> dict[str, str | int]: ...


class SentenceTransformerEmbedding:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        self._model_lock = threading.Lock()

    @staticmethod
    def name() -> str:
        return "cyber_ir_sentence_transformer"

    def __call__(self, input: list[str]) -> list[list[float]]:
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(self.model_name)
        vectors = self._model.encode(input, normalize_embeddings=True)
        return vectors.tolist()

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self(input)

    @staticmethod
    def is_legacy() -> bool:
        return False

    @staticmethod
    def supported_spaces() -> list[str]:
        return ["cosine", "l2", "ip"]

    def get_config(self) -> dict[str, str]:
        return {"model_name": self.model_name}

    @staticmethod
    def build_from_config(config: dict[str, str]) -> SentenceTransformerEmbedding:
        return SentenceTransformerEmbedding(config["model_name"])


class HashEmbedding:
    """Small deterministic embedding for tests; not used by default in production."""

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

    @staticmethod
    def name() -> str:
        return "cyber_ir_hash"

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [list(_hash_embed(text, self.dimensions)) for text in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self(input)

    @staticmethod
    def is_legacy() -> bool:
        return False

    @staticmethod
    def supported_spaces() -> list[str]:
        return ["cosine", "l2", "ip"]

    def get_config(self) -> dict[str, int]:
        return {"dimensions": self.dimensions}

    @staticmethod
    def build_from_config(config: dict[str, int]) -> HashEmbedding:
        return HashEmbedding(config["dimensions"])
