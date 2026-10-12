"""Day24: Vietnamese BM25 + BGE-M3/Qdrant 1.9, merged by reciprocal rank fusion."""
from dataclasses import dataclass

from config import (BM25_TOP_K, COLLECTION_NAME, DENSE_TOP_K, EMBEDDING_DIM,
                    EMBEDDING_MODEL, HYBRID_TOP_K, QDRANT_HOST, QDRANT_PORT)


@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict
    method: str


def segment_vietnamese(text: str) -> list[str]:
    from underthesea import word_tokenize
    return word_tokenize(text.lower(), format="text").split()


def reciprocal_rank_fusion(lists: list[list[SearchResult]], top_k: int = HYBRID_TOP_K):
    fused = {}
    for results in lists:
        for rank, result in enumerate(results, start=1):
            identity = (result.metadata.get("source"), result.metadata.get("chunk_index"), result.text)
            score, original = fused.get(identity, (0.0, result))
            fused[identity] = (score + 1 / (60 + rank), original)
    ranked = sorted(fused.values(), key=lambda item: item[0], reverse=True)
    return [SearchResult(doc.text, score, doc.metadata, "hybrid")
            for score, doc in ranked[:max(0, top_k)]]


class HybridSearch:
    def __init__(self):
        import torch  # Load Windows torch DLLs first.
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=60)
        self.client.get_collections()
        self.encoder = SentenceTransformer(EMBEDDING_MODEL)

    def index(self, chunks: list[dict]) -> None:
        from rank_bm25 import BM25Okapi
        from qdrant_client.models import Distance, PointStruct, VectorParams
        if not chunks:
            raise ValueError("Cannot index an empty corpus")
        self.chunks = chunks
        self.bm25 = BM25Okapi([segment_vietnamese(c["text"]) for c in chunks])
        vectors = self.encoder.encode([c["text"] for c in chunks], batch_size=8,
                                      normalize_embeddings=True, show_progress_bar=True)
        # Finish embedding before replacing this lab's collection.
        self.client.recreate_collection(collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE))
        points = [PointStruct(id=i, vector=vector.tolist(),
                              payload={**chunk["metadata"], "text": chunk["text"]})
                  for i, (chunk, vector) in enumerate(zip(chunks, vectors))]
        self.client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)

    def search(self, question: str, top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
        if top_k <= 0:
            return []
        scores = self.bm25.get_scores(segment_vietnamese(question))
        indices = sorted(range(len(scores)), key=lambda i: float(scores[i]), reverse=True)
        sparse = [SearchResult(self.chunks[i]["text"], float(scores[i]),
                               self.chunks[i]["metadata"], "bm25")
                  for i in indices[:BM25_TOP_K] if scores[i] > 0]
        vector = self.encoder.encode(question, normalize_embeddings=True).tolist()
        # Pinned qdrant-client 1.9 supports search(), not query_points().
        hits = self.client.search(collection_name=COLLECTION_NAME, query_vector=vector, limit=DENSE_TOP_K)
        dense = [SearchResult(hit.payload["text"], float(hit.score),
                              {k: v for k, v in hit.payload.items() if k != "text"}, "dense")
                 for hit in hits]
        return reciprocal_rank_fusion([sparse, dense], top_k)
