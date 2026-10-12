"""Day24 RAGAS evaluator: actual metrics and model provenance, no proxy scores."""
import math
from dataclasses import dataclass

from config import EVALUATOR_EMBEDDING_MODEL, EVALUATOR_MODEL, OPENAI_API_KEY

METRICS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")


@dataclass
class EvalResult:
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def evaluate_ragas(questions, answers, contexts, ground_truths) -> dict:
    if not (len(questions) == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError("Evaluation inputs must have equal lengths")
    if not questions:
        raise ValueError("Evaluation inputs must not be empty")
    if not OPENAI_API_KEY:
        raise ValueError("Configure OPENAI_API_KEY in Day24 .env before evaluation")
    import torch
    from datasets import Dataset
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import evaluate
    from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness
    from ragas.run_config import RunConfig

    llm = ChatOpenAI(model=EVALUATOR_MODEL, temperature=0, api_key=OPENAI_API_KEY)
    embeddings = OpenAIEmbeddings(model=EVALUATOR_EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
    dataset = Dataset.from_dict({"question": questions, "answer": answers,
                                 "contexts": contexts, "ground_truth": ground_truths})
    result = evaluate(dataset,
        metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()],
        llm=llm, embeddings=embeddings, raise_exceptions=True,
        run_config=RunConfig(timeout=180, max_retries=3, max_workers=4))
    records = result.to_pandas().to_dict(orient="records")
    if len(records) != len(questions):
        raise ValueError("RAGAS changed the question count")
    rows = []
    for index, record in enumerate(records):
        scores = {metric: float(record[metric]) for metric in METRICS}
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in scores.values()):
            raise ValueError(f"Invalid RAGAS scores at row {index}; do not replace with zeros")
        rows.append(EvalResult(**scores))
    return {"per_question": rows, "metadata": {
        "evaluator_models": [llm.model_name, embeddings.model]}, "evaluation_mode": "ragas"}
