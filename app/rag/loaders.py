from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class LoadedDocument:
    text: str
    metadata: dict[str, str | int]


def load_document(path: Path) -> list[LoadedDocument]:
    suffix = path.suffix.lower()
    base = {"filename": path.name, "path": str(path), "title": path.stem.replace("_", " ").title()}
    if suffix in {".md", ".txt"}:
        return [LoadedDocument(path.read_text(encoding="utf-8"), base)]
    if suffix == ".pdf":
        try:
            reader = PdfReader(str(path))
            return [
                LoadedDocument(page.extract_text() or "", {**base, "page": number})
                for number, page in enumerate(reader.pages, start=1)
                if page.extract_text()
            ]
        except Exception as exc:
            raise RuntimeError(f"Could not parse PDF {path}: {exc}") from exc
    raise ValueError(f"Unsupported document type: {path.suffix}")


def load_directory(path: Path) -> list[LoadedDocument]:
    if not path.exists():
        raise FileNotFoundError(f"Knowledge base does not exist: {path}")
    supported = {".md", ".txt", ".pdf"}
    documents: list[LoadedDocument] = []
    for file_path in sorted(item for item in path.rglob("*") if item.suffix.lower() in supported):
        documents.extend(load_document(file_path))
    return documents

