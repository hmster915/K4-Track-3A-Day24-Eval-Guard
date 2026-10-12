from __future__ import annotations

"""Phase C: Production Guardrails — Presidio PII + NeMo Guardrails + P95 Latency."""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GUARDRAILS_CONFIG_DIR, PRESIDIO_LANGUAGE


# ─── Task 9a: Presidio PII Detection ─────────────────────────────────────────

def setup_presidio():
    """Khởi tạo Presidio với các recognizer PII cần cho bài lab.

    Custom recognizers thêm vào:
        VN_CCCD  — số CCCD 12 chữ số hoặc CMND 9 chữ số
        VN_PHONE — số điện thoại Việt Nam (0[3-9]xxxxxxxx)

    """
    from presidio_analyzer import (AnalyzerEngine, RecognizerRegistry, Pattern,
                                   PatternRecognizer)
    from presidio_anonymizer import AnonymizerEngine
    from presidio_analyzer.nlp_engine import NoOpNlpEngine

    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[
            Pattern("CCCD 12 digits", r"\b\d{12}\b", 0.9),
            Pattern("CMND 9 digits",  r"\b\d{9}\b",  0.7),
        ],
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern("VN mobile", r"\b0[3-9]\d{8}\b", 0.9)],
    )
    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        patterns=[Pattern(
            "Email address",
            r"(?<![\w.+-])[\w.!#$%&'*+/=?^_`{|}~-]+@(?:[\w](?:[\w-]*[\w])?\.)+[A-Za-z]{2,}(?![\w.-])",
            0.9,
        )],
    )

    registry = RecognizerRegistry(
        recognizers=[cccd_recognizer, phone_recognizer, email_recognizer],
        supported_languages=[PRESIDIO_LANGUAGE],
    )

    nlp_engine = NoOpNlpEngine(models=[{"lang_code": PRESIDIO_LANGUAGE,
                                        "model_name": "no_op"}])
    analyzer = AnalyzerEngine(registry=registry, nlp_engine=nlp_engine,
                              supported_languages=[PRESIDIO_LANGUAGE])
    anonymizer = AnonymizerEngine()
    return analyzer, anonymizer


def pii_scan(text: str, analyzer=None, anonymizer=None) -> dict:
    """Task 9a: Quét PII trong văn bản bằng Presidio.

    Returns:
        {
          "has_pii":    bool,
          "entities":   [{"type": str, "text": str, "score": float, "start": int, "end": int}],
          "anonymized": str,   # text với PII được thay bằng <TYPE>
        }
    """
    if not isinstance(text, str):
        raise TypeError("PII scan input must be a string")
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    results = analyzer.analyze(text=text, language=PRESIDIO_LANGUAGE)
    entities = []
    for result in results:
        start, end = int(result.start), int(result.end)
        if not 0 <= start < end <= len(text):
            raise ValueError("Presidio returned an invalid entity span")
        entities.append({
            "type": result.entity_type, "text": text[start:end],
            "score": round(float(result.score), 3), "start": start, "end": end,
        })
    entities.sort(key=lambda row: (row["start"], row["end"], row["type"]))
    if not results:
        return {"has_pii": False, "entities": [], "anonymized": text}
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results).text
    return {"has_pii": True, "entities": entities, "anonymized": anonymized}


def _rail_decision(result, *, stage: str) -> tuple[bool, str]:
    """Read the actual NeMo stop decision from activated rail logs."""
    log = getattr(result, "log", None)
    if log is None or not hasattr(log, "activated_rails"):
        raise ValueError(f"NeMo {stage} response did not include activated_rails logging")
    activated = log.activated_rails
    if activated is None:
        raise ValueError(f"NeMo {stage} activated_rails is unavailable")
    stopped = [rail for rail in activated if bool(getattr(rail, "stop", False))]
    return bool(stopped), f"nemo_{stage}_rail" if stopped else None


def _response_text(result) -> str:
    response = getattr(result, "response", None)
    if isinstance(response, str):
        text = response
    elif isinstance(response, list) and response and isinstance(response[0], dict):
        text = response[0].get("content", "")
    else:
        text = ""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("NeMo returned an empty or invalid response")
    return text


# ─── Task 9b + 11: NeMo Guardrails ───────────────────────────────────────────

def setup_nemo_rails():
    """Khởi tạo NeMo Guardrails từ guardrails/config.yml. (Đã implement sẵn)

    Config directory: guardrails/
        config.yml  — model + rails config
        rails.co    — câu từ chối Colang 1.0; built-in self-check flows được bật trong YAML
    """
    from nemoguardrails import RailsConfig, LLMRails
    config = RailsConfig.from_path(GUARDRAILS_CONFIG_DIR)
    rails  = LLMRails(config)
    return rails


async def check_input_rail(text: str, rails=None) -> dict:
    """Task 9b: Kiểm tra input qua NeMo input rails (topic guard + jailbreak guard).

    Returns:
        {
          "allowed":        bool,
          "blocked_reason": str | None,
          "response":       str,          # NeMo's raw response
        }
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input rail requires non-empty text")
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": text}],
        options={"rails": ["input"], "log": {"activated_rails": True}},
    )
    blocked, reason = _rail_decision(result, stage="input")
    return {"allowed": not blocked, "blocked_reason": reason,
            "response": _response_text(result)}


async def check_output_rail(question: str, answer: str, rails=None) -> dict:
    """Task 11: Kiểm tra LLM output qua NeMo output rails trước khi trả về user.

    NeMo output rails hoạt động trong context của cả cuộc hội thoại (input + output).
    Kiểm tra PII và nội dung nhạy cảm. Self-check này không thay RAGAS faithfulness
    hoặc kiểm tra factual accuracy với retrieved contexts.

    Returns:
        {
          "safe":           bool,
          "flagged_reason": str | None,
          "final_answer":   str,          # answer đã qua guard (có thể bị redact)
        }
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Output rail requires a non-empty question")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Output rail requires a non-empty answer")
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": question},
                  {"role": "assistant", "content": answer}],
        options={"rails": ["output"], "log": {"activated_rails": True}},
    )
    flagged, reason = _rail_decision(result, stage="output")
    guarded_response = _response_text(result)
    if not flagged:
        return {"safe": True, "flagged_reason": None, "final_answer": answer}
    fallback = (
        "Xin lỗi, tôi không thể cung cấp nội dung này. Tôi chỉ hỗ trợ chính sách nội bộ "
        "của công ty và không cung cấp dữ liệu cá nhân, thông tin nhân viên bí mật hoặc mật khẩu."
    )
    final_answer = guarded_response if guarded_response != answer else fallback
    return {"safe": False, "flagged_reason": reason, "final_answer": final_answer}


# ─── Task 10: Adversarial Test Suite ─────────────────────────────────────────

def run_adversarial_suite(adversarial_set: list[dict], rails=None,
                           analyzer=None, anonymizer=None) -> list[dict]:
    """Task 10: Chạy input cases qua guard stack; expected chỉ dùng sau quyết định.

    Guard stack order:
        1. pii_scan()         → block nếu has_pii (cho category pii_injection)
        2. check_input_rail() → block nếu jailbreak / off-topic / prompt injection

    Returns:
        list of {
          "id": int, "category": str, "input": str,
          "expected": "blocked"|"allowed",
          "actual":   "blocked"|"allowed",
          "blocked_by": str | None,       # "presidio" | "nemo_input" | None
          "passed": bool,
        }
    """
    if not isinstance(adversarial_set, list):
        raise TypeError("Input suite must be a list")
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def run_all():
        rows = []
        for item in adversarial_set:
            user_text = item.get("input")
            if not isinstance(user_text, str) or not user_text.strip():
                raise ValueError(f"Input case {item.get('id')} has no text")
            pii = pii_scan(user_text, analyzer, anonymizer)
            blocked_by = "presidio" if pii["has_pii"] else None
            if blocked_by is None:
                decision = await check_input_rail(user_text, rails)
                if not decision["allowed"]:
                    blocked_by = "nemo_input"
            actual = "blocked" if blocked_by else "allowed"
            expected = item.get("expected")
            rows.append({
                "id": item["id"], "category": item["category"], "input": user_text,
                "expected": expected, "actual": actual, "blocked_by": blocked_by,
                "passed": actual == expected,
            })
        return rows

    results = asyncio.run(run_all())
    passed = sum(row["passed"] for row in results)
    print(f"Input guard suite: {passed}/{len(results)} expected decisions matched")
    return results


# ─── Task 12: P95 Latency Measurement ────────────────────────────────────────

def measure_p95_latency(test_inputs: list[str], n_runs: int = 20,
                         rails=None, analyzer=None, anonymizer=None) -> dict:
    """Task 12: measure INPUT layers sequentially, not end-to-end guard/RAG latency.

    Reuse engines. Inside ONE event loop, execute two real warm-up calls per layer,
    excluded from samples. Then collect exactly n_runs timed samples (cycle clean
    inputs), always measuring BOTH PII and NeMo input even if PII blocks.
    Use perf_counter; keep raw milliseconds. summarize_latency() supplies linear
    percentiles at (n - 1) * q. Submission requires n_runs >= 20.
    Short-circuit request timing, RAG and output timing are outside this scope.
    """
    from src.experiment_support import summarize_latency

    if not test_inputs or any(not isinstance(value, str) or not value.strip() for value in test_inputs):
        raise ValueError("Latency measurement requires non-empty input strings")
    if n_runs < 20:
        raise ValueError("At least 20 timed latency samples are required")
    if analyzer is None or anonymizer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def measure():
        for index in range(2):
            value = test_inputs[index % len(test_inputs)]
            pii_scan(value, analyzer, anonymizer)
            await check_input_rail(value, rails)
        samples = []
        for index in range(n_runs):
            value = test_inputs[index % len(test_inputs)]
            start = time.perf_counter()
            pii_scan(value, analyzer, anonymizer)
            presidio_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            await check_input_rail(value, rails)
            nemo_ms = (time.perf_counter() - start) * 1000
            total_ms = presidio_ms + nemo_ms
            if min(presidio_ms, nemo_ms, total_ms) <= 0:
                raise ValueError("Measured latency samples must be positive")
            samples.append({"presidio_ms": presidio_ms,
                            "nemo_input_ms": nemo_ms,
                            "input_guard_ms": total_ms})
        return samples

    return summarize_latency(asyncio.run(measure()), warmup_runs=2)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "c", *sys.argv[1:]]))
