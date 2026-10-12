from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH, OPENAI_API_KEY, GENERATION_MODEL, EMBEDDING_MODEL


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    lengths = {len(questions), len(answers), len(contexts), len(ground_truths)}
    if len(lengths) != 1:
        raise ValueError("questions, answers, contexts, and ground_truths must have equal lengths")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required for live RAGAS evaluation")
    if not questions:
        raise ValueError("At least one question is required for evaluation")

    from datasets import Dataset
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    llm = ChatOpenAI(model=GENERATION_MODEL, api_key=OPENAI_API_KEY, temperature=0)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })
    evaluated = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=True,
    ).to_pandas()

    metric_names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    per_question = []
    for index, row in evaluated.iterrows():
        metric_values = {name: float(row[name]) for name in metric_names}
        per_question.append(EvalResult(
            question=questions[index], answer=answers[index], contexts=contexts[index],
            ground_truth=ground_truths[index], **metric_values,
        ))
    aggregates = {name: float(evaluated[name].mean()) for name in metric_names}
    return {
        **aggregates,
        "per_question": per_question,
        "metadata": {"evaluator_models": [GENERATION_MODEL, EMBEDDING_MODEL]},
    }


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    diagnostic_tree = {
        "faithfulness": ("Answer contains claims unsupported by context", "Tighten the grounded answer prompt"),
        "context_recall": ("Retrieved context misses relevant evidence", "Improve chunking or hybrid retrieval"),
        "context_precision": ("Retrieved context contains irrelevant passages", "Improve reranking or metadata filters"),
        "answer_relevancy": ("Answer does not directly address the question", "Improve the answer prompt"),
    }
    ordered = sorted(eval_results, key=lambda r: (
        (r.faithfulness + r.answer_relevancy + r.context_precision + r.context_recall) / 4
    ))[:max(0, bottom_n)]
    failures = []
    for row in ordered:
        scores = {name: float(getattr(row, name)) for name in diagnostic_tree}
        worst = min(scores, key=scores.get)
        diagnosis, fix = diagnostic_tree[worst]
        failures.append({"question": row.question, "worst_metric": worst,
                         "score": scores[worst], "avg_score": sum(scores.values()) / 4,
                         "diagnosis": diagnosis, "suggested_fix": fix})
    return failures


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
