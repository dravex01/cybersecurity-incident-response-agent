from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 850, overlap: int = 120) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    clean = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not clean:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        target = min(start + chunk_size, len(clean))
        end = target
        if target < len(clean):
            candidates = [clean.rfind("\n\n", start, target), clean.rfind(". ", start, target)]
            boundary = max(candidates)
            if boundary > start + chunk_size // 2:
                end = boundary + (0 if clean[boundary : boundary + 2] == "\n\n" else 1)
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(clean):
            break
        start = max(start + 1, end - overlap)
    return chunks

