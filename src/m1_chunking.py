from __future__ import annotations

"""
Module 1: Advanced Chunking Strategies
=======================================
Implement semantic, hierarchical, và structure-aware chunking.
So sánh với basic chunking (baseline) để thấy improvement.

Test: pytest tests/test_m1.py
"""

import os, sys, glob, re
from dataclasses import dataclass, field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (DATA_DIR, HIERARCHICAL_PARENT_SIZE, HIERARCHICAL_CHILD_SIZE,
                    SEMANTIC_THRESHOLD)


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    parent_id: str | None = None


def _extract_pdf_text(path: str) -> str:
    """Extract text layer từ PDF. Trả về "" nếu PDF là scan ảnh (không có text)."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


def load_documents(data_dir: str = DATA_DIR) -> list[dict]:
    """Load tất cả markdown và PDF (có text layer) từ data/. (Đã implement sẵn)

    - .md: đọc trực tiếp.
    - .pdf: trích text layer bằng pypdf. PDF scan ảnh (không có text) bị bỏ qua
      kèm cảnh báo — RAG text-based không xử lý được scan nếu chưa OCR.
    """
    docs = []
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(fp, encoding="utf-8") as f:
            docs.append({"text": f.read(), "metadata": {"source": os.path.basename(fp)}})

    for fp in sorted(glob.glob(os.path.join(data_dir, "*.pdf"))):
        text = _extract_pdf_text(fp)
        if text:
            docs.append({"text": text, "metadata": {"source": os.path.basename(fp)}})
        else:
            print(f"  ⚠️  Bỏ qua {os.path.basename(fp)}: PDF scan ảnh, không có text layer (cần OCR).")

    return docs


# ─── Baseline: Basic Chunking (để so sánh) ──────────────


def chunk_basic(text: str, chunk_size: int = 500, metadata: dict | None = None) -> list[Chunk]:
    """
    Basic chunking: split theo paragraph (\\n\\n).
    Đây là baseline — KHÔNG phải mục tiêu của module này.
    (Đã implement sẵn)
    """
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for i, para in enumerate(paragraphs):
        if len(current) + len(para) > chunk_size and current:
            chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
            current = ""
        current += para + "\n\n"
    if current.strip():
        chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
    return chunks


# ─── Strategy 1: Semantic Chunking ───────────────────────


def chunk_semantic(text: str, threshold: float = SEMANTIC_THRESHOLD,
                   metadata: dict | None = None) -> list[Chunk]:
    """
    Split text by sentence similarity — nhóm câu cùng chủ đề.
    Tốt hơn basic vì không cắt giữa ý.
    """
    from config import OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIM

    metadata = metadata or {}
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n\s*\n", text) if s.strip()]
    if not sentences:
        return []
    if len(sentences) == 1 or not OPENAI_API_KEY:
        return [Chunk(s, {**metadata, "strategy": "semantic_fallback", "chunk_index": i})
                for i, s in enumerate(sentences)]

    from openai import OpenAI
    import numpy as np

    client = OpenAI(api_key=OPENAI_API_KEY)
    vectors: list[list[float]] = []
    for start in range(0, len(sentences), 128):
        response = client.embeddings.create(
            model=EMBEDDING_MODEL, dimensions=EMBEDDING_DIM, input=sentences[start:start + 128]
        )
        vectors.extend(item.embedding for item in response.data)

    groups: list[list[str]] = [[sentences[0]]]
    for index in range(1, len(sentences)):
        left, right = np.asarray(vectors[index - 1]), np.asarray(vectors[index])
        similarity = float(np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right) + 1e-9))
        if similarity < threshold:
            groups.append([sentences[index]])
        else:
            groups[-1].append(sentences[index])
    return [Chunk(" ".join(group), {**metadata, "strategy": "semantic", "chunk_index": i})
            for i, group in enumerate(groups)]


# ─── Strategy 2: Hierarchical Chunking ──────────────────


def chunk_hierarchical(text: str, parent_size: int = HIERARCHICAL_PARENT_SIZE,
                       child_size: int = HIERARCHICAL_CHILD_SIZE,
                       metadata: dict | None = None) -> tuple[list[Chunk], list[Chunk]]:
    """
    Parent-child hierarchy: retrieve child (precision) → return parent (context).
    Đây là default recommendation cho production RAG.

    Returns:
        (parents, children) — mỗi child có parent_id link đến parent.
    """
    if parent_size < 1 or child_size < 1:
        raise ValueError("parent_size and child_size must be positive")
    metadata = metadata or {}
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]

    def split_oversized(value: str, limit: int) -> list[str]:
        pieces = []
        remaining = value.strip()
        while len(remaining) > limit:
            boundary = remaining.rfind(" ", 0, limit + 1)
            if boundary < max(1, limit // 2):
                boundary = limit
            pieces.append(remaining[:boundary].strip())
            remaining = remaining[boundary:].strip()
        if remaining:
            pieces.append(remaining)
        return pieces

    parent_texts: list[str] = []
    current = ""
    for paragraph in paragraphs:
        for piece in split_oversized(paragraph, parent_size):
            candidate = f"{current}\n\n{piece}" if current else piece
            if len(candidate) > parent_size and current:
                parent_texts.append(current)
                current = piece
            else:
                current = candidate
    if current:
        parent_texts.append(current)

    parents: list[Chunk] = []
    children: list[Chunk] = []
    for parent_index, parent_text in enumerate(parent_texts):
        parent_id = f"parent_{parent_index}"
        parents.append(Chunk(parent_text, {**metadata, "chunk_type": "parent", "parent_id": parent_id,
                                           "chunk_index": parent_index}, parent_id))
        child_parts = []
        child_current = ""
        for paragraph in [part.strip() for part in parent_text.split("\n\n") if part.strip()]:
            for piece in split_oversized(paragraph, child_size):
                candidate = f"{child_current}\n\n{piece}" if child_current else piece
                if len(candidate) > child_size and child_current:
                    child_parts.append(child_current)
                    child_current = piece
                else:
                    child_current = candidate
        if child_current:
            child_parts.append(child_current)
        for child_index, child_text in enumerate(child_parts):
            children.append(Chunk(child_text, {**metadata, "chunk_type": "child",
                                               "chunk_index": child_index, "parent_id": parent_id}, parent_id))
    return parents, children


# ─── Strategy 3: Structure-Aware Chunking ────────────────


def chunk_structure_aware(text: str, metadata: dict | None = None) -> list[Chunk]:
    """
    Parse markdown headers → chunk theo logical structure.
    Giữ nguyên tables, code blocks, lists — không cắt giữa chừng.
    """
    metadata = metadata or {}
    sections: list[Chunk] = []
    current_header = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            content = "\n".join(current_lines).strip()
            section_text = "\n\n".join(part for part in (current_header, content) if part)
            if section_text:
                sections.append(Chunk(section_text, {**metadata, "section": current_header,
                                                      "strategy": "structure", "chunk_index": len(sections)}))
            current_header, current_lines = line.strip(), []
        else:
            current_lines.append(line)
    content = "\n".join(current_lines).strip()
    section_text = "\n\n".join(part for part in (current_header, content) if part)
    if section_text:
        sections.append(Chunk(section_text, {**metadata, "section": current_header,
                                              "strategy": "structure", "chunk_index": len(sections)}))
    return sections


# ─── A/B Test: Compare All Strategies ────────────────────


def compare_strategies(documents: list[dict]) -> dict:
    """
    Run all strategies on documents and compare.
    (Đã implement sẵn — sẽ hoạt động khi bạn implement 3 strategies ở trên)
    """
    def _stats(chunk_list):
        lengths = [len(c.text) for c in chunk_list]
        if not lengths:
            return {"count": 0, "avg_len": 0, "min_len": 0, "max_len": 0}
        return {
            "count": len(lengths),
            "avg_len": round(sum(lengths) / len(lengths)),
            "min_len": min(lengths),
            "max_len": max(lengths),
        }

    all_text = "\n\n".join(d["text"] for d in documents)
    meta = {"source": "all"}

    basic = chunk_basic(all_text, metadata=meta)
    semantic = chunk_semantic(all_text, metadata=meta)
    parents, children = chunk_hierarchical(all_text, metadata=meta)
    structure = chunk_structure_aware(all_text, metadata=meta)

    results = {
        "basic": _stats(basic),
        "semantic": _stats(semantic),
        "hierarchical": {**_stats(children), "parents": len(parents)},
        "structure": _stats(structure),
    }

    print(f"{'Strategy':<15} {'Chunks':>7} {'Avg':>5} {'Min':>5} {'Max':>5}")
    for name, s in results.items():
        print(f"{name:<15} {s['count']:>7} {s['avg_len']:>5} {s['min_len']:>5} {s['max_len']:>5}")

    return results


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")
    results = compare_strategies(docs)
    for name, stats in results.items():
        print(f"  {name}: {stats}")
