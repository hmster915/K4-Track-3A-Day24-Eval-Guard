from __future__ import annotations

"""Module 2: Vietnamese BM25 + online dense embeddings + Qdrant + RRF."""

from dataclasses import dataclass
import math
import re

from config import (
    OPENAI_API_KEY, QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, EMBEDDING_MODEL,
    EMBEDDING_DIM, BM25_TOP_K, DENSE_TOP_K, HYBRID_TOP_K,
)


@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict
    method: str


def segment_vietnamese(text: str) -> str:
    """Word-segment Vietnamese and normalize underscore-joined compounds."""
    try:
        from underthesea import word_tokenize
        return word_tokenize(text, format="text").replace("_", " ")
    except Exception:
        return re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)


class BM25Search:
    def __init__(self):
        self.corpus_tokens: list[list[str]] = []
        self.documents: list[dict] = []
        self.bm25 = None

    def index(self, chunks: list[dict]) -> None:
        self.documents = list(chunks)
        self.corpus_tokens = [segment_vietnamese(c["text"]).lower().split() for c in chunks]
        if self.corpus_tokens:
            from rank_bm25 import BM25Okapi
            self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self.bm25 = None

    def search(self, query: str, top_k: int = BM25_TOP_K) -> list[SearchResult]:
        if self.bm25 is None or top_k <= 0:
            return []
        tokens = segment_vietnamese(query).lower().split()
        scores = self.bm25.get_scores(tokens)
        order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))
        return [SearchResult(self.documents[i]["text"], float(scores[i]),
                             dict(self.documents[i].get("metadata", {})), "bm25")
                for i in order[:top_k] if math.isfinite(float(scores[i])) and scores[i] > 0]


class DenseSearch:
    """Qdrant vector search using OpenAI embeddings; no local model is loaded."""
    def __init__(self):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required for online dense embeddings; configure it locally first.")
        from openai import OpenAI
        from qdrant_client import QdrantClient

        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=10)
        self.client.get_collections()
        self._encoder = OpenAI(api_key=OPENAI_API_KEY)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 128):
            response = self._encoder.embeddings.create(
                model=EMBEDDING_MODEL, dimensions=EMBEDDING_DIM, input=texts[start:start + 128]
            )
            vectors.extend(item.embedding for item in response.data)
        return vectors

    def index(self, chunks: list[dict], collection: str = COLLECTION_NAME) -> None:
        from qdrant_client.models import Distance, PointStruct, VectorParams

        self.client.recreate_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        vectors = self._embed([chunk["text"] for chunk in chunks])
        for start in range(0, len(chunks), 64):
            points = [
                PointStruct(
                    id=i,
                    vector=vectors[i],
                    payload={**chunks[i].get("metadata", {}), "text": chunks[i]["text"]},
                )
                for i in range(start, min(start + 64, len(chunks)))
            ]
            if points:
                self.client.upsert(collection_name=collection, points=points, wait=True)

    def search(self, query: str, top_k: int = DENSE_TOP_K,
               collection: str = COLLECTION_NAME) -> list[SearchResult]:
        if top_k <= 0:
            return []
        vector = self._embed([query])[0]
        hits = self.client.search(collection_name=collection, query_vector=vector, limit=top_k)
        results = []
        for hit in hits:
            payload = dict(hit.payload or {})
            text = payload.pop("text", "")
            if text:
                results.append(SearchResult(text, float(hit.score), payload, "dense"))
        return results


def _result_key(result: SearchResult) -> tuple:
    meta = result.metadata
    return (meta.get("source"), meta.get("chunk_index"), meta.get("parent_id"), result.text)


def reciprocal_rank_fusion(results_list: list[list[SearchResult]], k: int = 60,
                           top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
    if k <= 0:
        raise ValueError("RRF k must be positive")
    fused: dict[tuple, tuple[float, SearchResult]] = {}
    for ranked in results_list:
        for rank, result in enumerate(ranked, start=1):
            key = _result_key(result)
            score, original = fused.get(key, (0.0, result))
            fused[key] = (score + 1.0 / (k + rank), original)
    ordered = sorted(fused.values(), key=lambda item: item[0], reverse=True)[:max(0, top_k)]
    return [SearchResult(result.text, score, dict(result.metadata), "hybrid")
            for score, result in ordered]


class HybridSearch:
    """Combines BM25 and Qdrant dense results with reciprocal-rank fusion."""
    def __init__(self):
        self.bm25 = BM25Search()
        self.dense = DenseSearch()

    def index(self, chunks: list[dict]) -> None:
        self.bm25.index(chunks)
        self.dense.index(chunks)

    def search(self, query: str, top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
        lexical = self.bm25.search(query, top_k=BM25_TOP_K)
        dense = self.dense.search(query, top_k=DENSE_TOP_K)
        return reciprocal_rank_fusion([lexical, dense], top_k=top_k)
