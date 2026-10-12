# K4 Track 3A — Progress Checklist

Track each item with a named owner and evidence. Mark an item complete only after confirming the actual file, command result, or live artifact. Record contributions and run details in `doc/TEAM.md` and reports.

## Scan and current baseline

- [x] Scanned all 38 Markdown files in this lab: assignment/guidance, rubric, rules, checkpoint and submission documents, TEAM/report templates, and 25 corpus files under `data/`.
- [x] Identified `data/` Markdown as RAG source corpus. Keep old/new versions (including 2023/2024 leave policy and password v1/v2) because version and negation conflicts are intentional evaluation cases. Use synthetic test PII only.
- [x] Python 3.11 project virtual environment exists; `pip check` passes.
- [x] Docker Desktop is running; Qdrant `qdrant/qdrant:v1.9.7` is healthy and has 120 indexed points.
- [x] Restored and completed `src/m1_chunking.py` through `src/m5_enrichment.py` from the Day 18 student repo, adapting embeddings/reranking to the online OpenAI provider.
- [x] Created ignored project `.env` from `.env.example`; the key is configured locally and was successfully used by the live run. No secret value is recorded here.
- [x] Generated `artifacts/answers_50q.json` with the live setup; verified the artifact against all 50 source questions.
- [x] Current dependency check: project Python is 3.11.9; NumPy 1.26.4 and PyArrow 20.0.0 are installed, `pip check` passes, and imports for RAGAS, NeMo Guardrails, Presidio, spaCy, OpenAI and dotenv succeed.
- [x] spaCy `en_core_web_lg` 3.8.0 downloaded to the project environment and successfully loaded.
- [x] MSVC Build Tools are installed and verified from the configured compiler environment: MSVC 14.51 / compiler 19.51.36260.

## CP0 — Prepare before class

- [x] Create/confirm a Python 3.11 virtual environment in this project and run `pip check` (currently passes).
- [x] Install full runtime dependencies using the project constraints; `pip check` and imports for RAGAS, NeMo Guardrails, Presidio, spaCy, OpenAI and dotenv pass.
- [x] In the build shell, `where.exe cl` and `cl` show MSVC 14+ (verified: MSVC 14.51 / compiler 19.51.36260).
- [x] Download spaCy `en_core_web_lg` and verify it loads.
- [x] Configure retrieval embeddings and reranking to use the OpenAI API instead of downloading/running local models. The modules use `text-embedding-3-small` (1024 dimensions) and `gpt-4o-mini`; the live run succeeded.
- [x] Start Qdrant using `infra/docker-compose.yml` (pinned image `qdrant/qdrant:v1.9.7`) and confirm it is healthy on port 6333 (Compose service `infra-qdrant-1` is running; `http://localhost:6333/healthz` returned HTTP 200 on 2026-10-12).
- [x] Restore and adapt the five previous-lab modules in `src/`: `m1_chunking.py`, `m2_search.py`, `m3_rerank.py`, `m4_eval.py`, `m5_enrichment.py`. Source: `hmster915/K4-Track3A-Day18-Production-RAG`; interfaces match `doc/PIPELINE_INTERFACE.md`, and setup does not call `pipeline.py`. Syntax/import and live integration checks passed.
- [x] Add `OPENAI_API_KEY` to the project-local, ignored `.env`; the live setup loaded it successfully. Never commit or share it, and keep `.env.example` free of secret values.
- [x] Run `python scripts/setup_answers.py --live` from the repo root (2026-10-12): enriched 120 chunks, indexed Qdrant, and generated 50 answers.
- [x] Verify `artifacts/answers_50q.json`: exactly 50 source IDs in source order; 20 factual, 20 multi_hop, 10 adversarial; source questions and ground truth unchanged; all answers and retrieved contexts are non-empty.
- [x] Verify generation provenance for all answers: `generation_mode=llm`; all rows include model ID `gpt-4o-mini-2024-07-18`. No extractive fallback rows.
- [ ] Fill the team/repo/leader/member/role details and readiness evidence plan in `doc/TEAM.md`.

## Phase A — RAGAS and failure analysis (CP1, 30 minutes)

- [x] Task 1: group into exactly 20 factual, 20 multi_hop and 10 adversarial questions.
- [x] Task 2: call m4 on all 50 answers; return 50 `RagasResult` entries, four finite metrics in [0,1], and evaluator model IDs from m4 metadata.
- [x] Task 3: create the ten lowest average-score rows with rank, ID, question, distribution, worst metric, diagnosis and suggested fix.
- [x] Task 4: build the worst-metric × distribution matrix for all questions; report means and choose the weakest distribution by lowest mean, not largest count.
- [x] Run the Phase A offline tests: `.venv\Scripts\python.exe -m pytest tests\test_phase_a.py -q` — 6 passed.
- [x] Run `.venv\Scripts\python.exe scripts\run_experiments.py --phase a --live` once (2026-10-12); saved and schema-validated live `artifacts/ragas_50q.json`.
- [x] Complete `doc/reports/failure_clusters.md` using the JSON; inspect representative question, answer, contexts and reference, including version/negation traps.
- [x] Reconcile the report’s 50 rows, four metrics, bottom ten, matrix and means with the artifact; preserve Task 3 diagnoses/fixes in export.

## Phase B — Pairwise judge and human calibration (CP2, 30 minutes)

- [x] Task 5: judge A/B/tie against the reference with valid reasoning and scores in [0,1].
- [x] Task 6: run both A/B and B/A with identical question/reference; map both results back to original A/B and calculate consensus.
- [x] Task 7: calculate Cohen’s κ on ten binary judgments and human labels in matching ID order; labels are integer 0/1.
- [x] Task 8: calculate position inconsistency and decisive-case verbosity win rate, with a cautious interpretation.
- [x] Use only pair IDs 1, 5, 12, 21, 41: candidate A from saved pipeline answer, B from supplied `model_answer`, reference from test-set `ground_truth`.
- [x] For ten binary judgments, evaluate the exact supplied `model_answer`; never send `human_label` or `human_note` to the judge. Join human labels only after predictions.
- [x] Run Phase B offline tests: `.venv\Scripts\python.exe -m pytest tests\test_phase_b.py tests\test_support.py tests\test_report_contracts.py -q` — 68 passed.
- [x] Run `.venv\Scripts\python.exe scripts\run_experiments.py --phase b --live`; saved real `artifacts/judge_results.json` after tightening the response schema on an initial invalid-response attempt.
- [x] Complete `doc/reports/bias_report.md` with five pair records, ten calibration rows in source order, κ/agreement calculations, evidence and limitations.

## Phase C — Guardrails, clean controls and latency (CP3, 30 minutes)

- [x] Task 9a implementation: Presidio detects and anonymizes/redacts Vietnamese ID numbers, phone numbers and email; returns entity types and positions. Installed-runtime scan of attacks detected fixture IDs 1–4 and had zero hits among the 8 clean controls.
- [x] Task 9b implementation: async input rail reads the actual activated-rail stop decision, reason and response; it does not infer block status from refusal wording.
- [x] Task 10 implementation: one suite accepts attacks and clean controls together, preserves input and uses expected labels only to calculate pass/fail after the guard decision.
- [x] Task 11 implementation: checks supplied outputs and preserves clean answers; blocked answers use NeMo's guarded response or a refusal fallback.
- [x] Task 12 implementation: sequential Presidio + NeMo input timing, two real warm-ups excluded, at least 20 positive timed samples and linear percentiles from raw samples.
- [x] Run Phase C offline tests: `.venv\Scripts\python.exe -m pytest tests\test_phase_c.py tests\test_support.py tests\test_report_contracts.py -q` — 72 passed.
- [x] Run `.venv\Scripts\python.exe scripts\run_experiments.py --phase c --live --latency-samples 20`; final real artifact saved at `artifacts/guard_results.json` (created_at `2026-10-12T16:08:15.202430+00:00`, after two prompt-calibration runs).
- [x] Final live batch: 20/20 attacks blocked, 8/8 clean controls allowed (false-positive rate 0), and all 4 output cases correct. Meets the 15/20 lab threshold and 18/20 bonus target.
- [x] Report measured input-layer latency: 20 samples, 2 warm-ups; sequential P95 931.35081 ms, over the 500 ms budget. RAG, output and full-request latency remain “chưa đo”; no full-stack inference from input timing.
- [x] Complete `doc/reports/blueprint.md` using A/B/C artifacts, actual latency, CI proposals, monitoring, privacy and limitations; CI/CD remains explicitly a proposal.

## CP4 — Reports, checker and submission

- [ ] Complete every member’s real role, evidence, checks, learning, limitations and AI/source disclosure in `doc/TEAM.md`; remove placeholders.
- [x] Complete all three reports from actual artifacts; report contract validation passes with no placeholders or blank required tables.
- [ ] Run `python scripts/check_lab.py` from the repo root and resolve issues. Latest run passes every check except `doc/TEAM.md`, which still has unresolved member/group identity placeholders.
- [ ] Do not rerun live integration after Phase B/C batches already created artifacts; prevent duplicate API calls/costs.
- [ ] Check for secrets and real personal data. Keep `.env`, virtual environments, model caches and installers out of the submission.
- [x] Scan tracked Git content for API-key-shaped values: none found; `.env` is not tracked. All existing experiment artifacts parse as JSON.
- [x] Verify all experiment artifacts are committed and not ignored; `artifacts/guard_results.json` is included in the CP3 commit.
- [ ] Record final submission commit SHA in TEAM after member/group details are supplied, ensure graders can access the repo, and have the team lead submit one link through the announced VLearn/coach channel.
- [ ] Confirm the lab date and applicable deadline from the coach announcement. The docs default to 23:59 on lab day, Asia/Ho_Chi_Minh.

## Scoring reminders

- Required 100 points: Phase A 30, Phase B 35, Phase C 35. Bonus up to 10: adversarial mean below factual +4; κ >0.6 on the correct ten answers +3; at least 18/20 attacks with 8/8 clean allowed +3.
- Mock tests do not replace live artifacts. Never invent scores, labels, model provenance, latency or execution claims.
- One shared team repository is submitted by the team lead. Individual contribution is documented in TEAM and Git history; follow the coach’s AI-use and late-submission rules.

## Suggested two-person work split

Replace Member 1/Member 2 with actual names in `doc/TEAM.md`. Keep one shared repository and review each other’s results before live runs and submission.

Current assignment confirmed by the user: teammate owns Member 1; user owns Member 2. Names and MSSVs have not yet been supplied, so they remain unfilled in TEAM.

### Member 1 — RAG preparation and Phase A

- [ ] Own the five previous-lab RAG modules (`m1`–`m5`) and verify their contracts against `doc/PIPELINE_INTERFACE.md`.
- [ ] Coordinate with Member 2 to confirm environment, Qdrant, models and local API configuration are ready; do not expose the key.
- [ ] Build and run `artifacts/answers_50q.json`; verify 50 IDs, distribution counts, contexts, references and generation provenance.
- [ ] Implement and own Phase A Tasks 1–4 in `src/phase_a_ragas.py`; run offline tests and the live Phase A experiment.
- [ ] Own `doc/reports/failure_clusters.md`, grounding analysis in the saved JSON and source contexts.
- [ ] Give Member 2 the verified answers artifact and record module/setup/Phase A contributions in TEAM.

### Member 2 — Environment, Phase B/C and integration

- [ ] Own full runtime dependency installation/import checks, compiler visibility, model download checks and Qdrant startup; record actual results in TEAM.
- [ ] Implement and own Phase B Tasks 5–8 in `src/phase_b_judge.py`; run offline tests and one live Phase B experiment after answers are ready.
- [ ] Own `doc/reports/bias_report.md`, using the exact pair sources and supplied `model_answer` calibration data.
- [ ] Implement and own Phase C Tasks 9a–12 in `src/phase_c_guard.py`; run offline tests and one live Phase C experiment.
- [ ] Own `doc/reports/blueprint.md`, keeping measured results distinct from proposals and unmeasured latency scopes.
- [ ] Coordinate the final checker, secret/artifact review, commit SHA, and submission handoff with the team lead; record actual work in TEAM.

### Shared handoffs and review gates

- [ ] Member 2 confirms CP0 environment readiness before Member 1 runs live answer generation.
- [ ] Member 1 reviews answer counts, IDs, contexts and generation metadata before Member 2 starts Phase B; both review before Phase A/B/C live runs to avoid paid reruns.
- [ ] Each owner gives the other person the exact run command, artifact path and observed result; the reviewer reconciles the report against the artifact.
- [ ] Both members complete their own `INDIVIDUAL` entry and verify the final repo/checker output before the team lead submits one link.
