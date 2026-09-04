import pytest
from pydantic import ValidationError

from app.config import Settings


def test_environment_parsing(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TOP_K", "7")
    monkeypatch.setenv("ENABLE_RERANKER", "false")
    settings = Settings(_env_file=None, chroma_path=tmp_path)
    assert settings.top_k == 7
    assert settings.enable_reranker is False


def test_overlap_must_be_smaller_than_chunk(monkeypatch) -> None:
    monkeypatch.delenv("CHUNK_SIZE", raising=False)
    monkeypatch.delenv("CHUNK_OVERLAP", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, chunk_size=400, chunk_overlap=400)

