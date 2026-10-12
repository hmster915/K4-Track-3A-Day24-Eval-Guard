"""Day24 multilingual cross-encoder reranking; errors propagate without lexical fallback."""
from dataclasses import dataclass

from config import RERANK_TOP_K


@dataclass
class RerankResult:
    text: str
    score: float
    metadata: dict


class CrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        import torch
        from sentence_transformers import CrossEncoder
        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def rerank(self, question: str, docs: list[dict], top_k: int = RERANK_TOP_K):
        if not docs or top_k <= 0:
            return []
        scores = self.model.predict([(question, doc["text"]) for doc in docs],
                                    batch_size=8, show_progress_bar=False)
        if len(scores) != len(docs):
            raise ValueError("Reranker changed the candidate count")
        ranked = sorted(zip(scores, docs), key=lambda item: float(item[0]), reverse=True)
        return [RerankResult(doc["text"], float(score), doc["metadata"])
                for score, doc in ranked[:top_k]]
