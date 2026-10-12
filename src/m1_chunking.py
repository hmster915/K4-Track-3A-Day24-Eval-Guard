"""Day24: read Markdown policies and split sections into parent/child chunks."""
from dataclasses import dataclass, field
from pathlib import Path
import re

from config import DATA_DIR, HIERARCHICAL_CHILD_SIZE, HIERARCHICAL_PARENT_SIZE


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    parent_id: str | None = None


def load_documents(data_dir: str = DATA_DIR) -> list[dict]:
    documents = []
    for path in sorted(Path(data_dir).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        title = next((line.lstrip("# ") for line in lines if line.startswith("# ")), path.stem)
        version = next((line.lstrip("> ") for line in lines if line.startswith(">")), "")
        documents.append({"text": text, "metadata": {
            "source": path.name, "title": title, "version": version}})
    if not documents:
        raise ValueError("No Markdown documents in Day24 data directory")
    return documents


def _split_text(text: str, limit: int) -> list[str]:
    """Prefer a word boundary when a section exceeds its character budget."""
    output = []
    text = text.strip()
    while len(text) > limit:
        boundary = text.rfind(" ", 0, limit + 1)
        if boundary <= 0:
            boundary = limit
        output.append(text[:boundary].strip())
        text = text[boundary:].strip()
    if text:
        output.append(text)
    return output


def chunk_hierarchical(text: str, metadata: dict | None = None,
                       parent_size: int = HIERARCHICAL_PARENT_SIZE,
                       child_size: int = HIERARCHICAL_CHILD_SIZE) -> tuple[list[Chunk], list[Chunk]]:
    if parent_size <= 0 or child_size <= 0 or child_size > parent_size:
        raise ValueError("Require 0 < child_size <= parent_size")
    metadata = dict(metadata or {})
    # Find headers, close the preceding section, continue until the document ends.
    sections = []
    heading, body = "", []
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s", line):
            if any(part.strip() for part in body):
                sections.append((heading, "\n".join(body)))
            heading, body = line.lstrip("# "), []
        else:
            body.append(line)
    if any(part.strip() for part in body):
        sections.append((heading, "\n".join(body)))
    parents, children = [], []
    for heading, section in sections:
        for parent_text in _split_text(section, parent_size):
            parent_id = f"{metadata.get('source', 'document')}:parent:{len(parents)}"
            parent_meta = {**metadata, "section": heading, "parent_id": parent_id}
            parents.append(Chunk(parent_text, parent_meta))
            for piece in _split_text(parent_text, child_size):
                children.append(Chunk(piece, {**parent_meta, "chunk_index": len(children)}, parent_id))
    return parents, children
