from __future__ import annotations

"""Phase A: RAGAS Production Evaluation — 50q, 3 distributions, cluster analysis."""

import json
import os
import sys
from dataclasses import asdict, dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH, ANSWERS_PATH, ARTIFACTS_DIR
from src.experiment_support import write_json

Distribution = str  # "factual" | "multi_hop" | "adversarial"

DIAGNOSTIC_TREE = {
    "faithfulness":      ("Có thể có khẳng định thiếu căn cứ; đối chiếu answer với contexts",
                          "Yêu cầu dẫn nguồn và từ chối khi context thiếu bằng chứng"),
    "context_recall":    ("Có thể thiếu ý cần thiết; đối chiếu contexts với reference",
                          "Kiểm tra ranh giới chunk và mở rộng retrieval cho câu nhiều bước"),
    "context_precision": ("Có thể có context không liên quan; kiểm tra từng chunk đã rerank",
                          "Đánh giá lại top-k và lọc phiên bản theo câu hỏi"),
    "answer_relevancy":  ("Có thể answer chưa trực tiếp đáp ứng câu hỏi",
                          "Kiểm tra câu hỏi/answer và yêu cầu trả lời đủ từng ý được hỏi"),
}


@dataclass
class RagasResult:
    question_id: int
    distribution: Distribution
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    @property
    def avg_score(self) -> float:
        return (self.faithfulness + self.answer_relevancy +
                self.context_precision + self.context_recall) / 4

    @property
    def worst_metric(self) -> str:
        scores = {
            "faithfulness":      self.faithfulness,
            "answer_relevancy":  self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall":    self.context_recall,
        }
        return min(scores, key=scores.get)


# ─── Đã implement sẵn ────────────────────────────────────────────────────────

@dataclass
class RagasEvaluation:
    """Task 2 output: measured rows plus model identifiers reported by m4."""
    results: list[RagasResult]
    evaluator_models: list[str]

def load_test_set_50q(path: str = TEST_SET_PATH) -> list[dict]:
    """Load 50q test set với 3 distributions."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_answers(path: str = ANSWERS_PATH) -> list[dict]:
    """Load pre-generated answers từ setup_answers.py."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"answers_50q.json không tìm thấy tại {path}\n"
            "→ Chạy trước: python scripts/setup_answers.py --live"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict]) -> dict:
    """Provided exporter: preserve the student-produced Task 3 rows verbatim."""
    per_dist: dict[str, dict] = {}
    for dist in ["factual", "multi_hop", "adversarial"]:
        subset = [r for r in results if r.distribution == dist]
        if subset:
            per_dist[dist] = {
                "count": len(subset),
                "faithfulness":      sum(r.faithfulness for r in subset) / len(subset),
                "answer_relevancy":  sum(r.answer_relevancy for r in subset) / len(subset),
                "context_precision": sum(r.context_precision for r in subset) / len(subset),
                "context_recall":    sum(r.context_recall for r in subset) / len(subset),
                "avg_score":         sum(r.avg_score for r in subset) / len(subset),
            }

    report = {
        "total_questions": len(results),
        "per_question": [asdict(r) for r in results],
        "per_distribution": per_dist,
        "failure_clusters": clusters,
        "bottom_10": bottom,
    }
    return report


def save_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict],
                        path: str = os.path.join(ARTIFACTS_DIR, "ragas_50q.json")) -> None:
    write_json(path, build_phase_a_report(results, clusters, bottom))



# ─── Tasks 1-4: Sinh viên implement ──────────────────────────────────────────

def group_by_distribution(test_set: list[dict]) -> dict[str, list[dict]]:
    """Task 1: preserve source order within the three distributions."""
    groups = {"factual": [], "multi_hop": [], "adversarial": []}
    for item in test_set:
        groups[item["distribution"]].append(item)
    return groups


def run_ragas_50q(answers: list[dict]) -> RagasEvaluation:
    """Task 2: evaluate once and preserve question order and evaluator IDs."""
    from src.m4_eval import evaluate_ragas
    from src.report_contracts import METRICS, score
    from src.experiment_support import model_ids

    raw = evaluate_ragas([a["question"] for a in answers], [a["answer"] for a in answers],
                         [a["contexts"] for a in answers], [a["ground_truth"] for a in answers])
    measured = raw["per_question"]
    if len(measured) != len(answers):
        raise ValueError("Evaluator must return one result per answer")
    models = raw["metadata"]["evaluator_models"]
    if not model_ids(models, "evaluator models"):
        raise ValueError("Evaluator must declare its actual models")
    results = []
    for answer, metrics in zip(answers, measured):
        values = {name: float(getattr(metrics, name)) for name in METRICS}
        for name, value in values.items():
            score(value, name)
        results.append(RagasResult(
            question_id=answer["id"], distribution=answer["distribution"],
            question=answer["question"], answer=answer["answer"], contexts=answer["contexts"],
            ground_truth=answer["ground_truth"], **values))
    return RagasEvaluation(results, models)


def bottom_10(results: list[RagasResult]) -> list[dict]:
    """Task 3: stable ascending mean; metric diagnoses are hypotheses to inspect."""
    output = []
    for rank, result in enumerate(sorted(results, key=lambda r: r.avg_score)[:10], start=1):
        diagnosis, fix = DIAGNOSTIC_TREE[result.worst_metric]
        output.append({"rank": rank, "question_id": result.question_id,
                       "distribution": result.distribution, "question": result.question,
                       "avg_score": round(result.avg_score, 4), "worst_metric": result.worst_metric,
                       "diagnosis": diagnosis, "suggested_fix": fix})
    return output


def cluster_analysis(results: list[RagasResult]) -> dict:
    """Task 4: weakest distribution is chosen by mean, not column counts."""
    distributions = ("factual", "multi_hop", "adversarial")
    if not results:
        raise ValueError("Cannot analyze an empty evaluation")
    matrix = {m: {d: 0 for d in distributions} for m in DIAGNOSTIC_TREE}
    for result in results:
        matrix[result.worst_metric][result.distribution] += 1
    means = {}
    for distribution in distributions:
        subset = [r for r in results if r.distribution == distribution]
        if subset:
            means[distribution] = sum(r.avg_score for r in subset) / len(subset)
    weakest = min(means, key=means.get)
    metric = max(matrix, key=lambda m: sum(matrix[m].values()))
    return {"matrix": matrix, "distribution_avg_scores": means,
            "dominant_failure_distribution": weakest, "dominant_failure_metric": metric,
            "insight": (f"Nhóm {weakest} có mean thấp nhất ({means[weakest]:.4f}); "
                        f"{metric} là metric thấp nhất xuất hiện nhiều nhất. "
                        "Matrix đếm mọi câu, không đồng nghĩa mọi câu đều lỗi. "
                        "Đọc answer/context/reference trước khi kết luận nguyên nhân. "
                        f"Gợi ý: {DIAGNOSTIC_TREE[metric][1]}.")}


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "a", *sys.argv[1:]]))
