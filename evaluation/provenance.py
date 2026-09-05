"""Reproducibility metadata without credentials, usernames, or environment dumps."""
from __future__ import annotations

import hashlib
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from app.config import Settings


def provenance(settings: Settings) -> dict:
    files = sorted(Path("app").rglob("*.py")) + sorted(Path("evaluation").glob("*.py"))
    files += sorted(Path("load_tests").glob("*.py"))
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.as_posix().encode())
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "platform": platform.system(), "python": platform.python_version(),
        "code_sha256": digest.hexdigest(),
        "dataset_sha256": hashlib.sha256(Path("evaluation/questions.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "packages": {name: version(name) for name in ("langgraph", "chromadb", "sentence-transformers", "streamlit")},
        "settings": settings.model_dump(mode="json", exclude={"ollama_base_url", "chroma_path", "knowledge_base_path"}),
    }
