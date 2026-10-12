# K4 Track 3A — Progress Checklist

Track each item with a named owner and evidence. Mark an item complete only after confirming the actual file, command result, or live artifact. Record contributions and run details in `doc/TEAM.md` and reports.

## Scan and current baseline

- [x] Scanned all 38 Markdown files in this lab: assignment/guidance, rubric, rules, checkpoint and submission documents, TEAM/report templates, and 25 corpus files under `data/`.
- [x] Identified `data/` Markdown as RAG source corpus. Keep old/new versions (including 2023/2024 leave policy and password v1/v2) because version and negation conflicts are intentional evaluation cases. Use synthetic test PII only.
- [x] Python 3.11 project virtual environment exists; `pip check` passes.
- [x] Docker Desktop is running; Qdrant `qdrant/qdrant:v1.9.7` is healthy. Member 1's CP1 batch used collection `lab24_production` with 116 chunks; an earlier CP0 check observed 120 points before the branch handoff.
- [x] Merged Member 1's `src/m1_chunking.py` through `src/m5_enrichment.py`: local BGE-M3 embeddings and BGE reranking; OpenAI remains the online generation/evaluation provider. Member 1 recorded model download/hash/runtime checks in TEAM and the Phase A report.
- [x] Created ignored project `.env` from `.env.example`; the key is configured locally and was successfully used by the live run. No secret value is recorded here.
- [x] Generated `artifacts/answers_50q.json` with the live setup; verified the artifact against all 50 source questions.
- [x] Current dependency check: project Python is 3.11.9; NumPy 1.26.4, PyArrow 17.0.0 and SentencePiece 0.2.2 are installed, `pip check` passes, and imports for the lab runtime succeed.
- [x] spaCy `en_core_web_lg` 3.8.0 downloaded to the project environment and successfully loaded.
- [x] MSVC Build Tools are installed and verified from the configured compiler environment: MSVC 14.51 / compiler 19.51.36260.

## CP0 — Prepare before class

- [x] Create/confirm a Python 3.11 virtual environment in this project and run `pip check` (currently passes).
- [x] Install full runtime dependencies using the project constraints; `pip check` and imports for RAGAS, NeMo Guardrails, Presidio, spaCy, OpenAI and dotenv pass.
- [x] In the build shell, `where.exe cl` and `cl` show MSVC 14+ (verified: MSVC 14.51 / compiler 19.51.36260).
- [x] Download spaCy `en_core_web_lg` and verify it loads.
- [x] Verify final retrieval/evaluation provenance: retrieval uses `BAAI/bge-m3` and `BAAI/bge-reranker-v2-m3` locally; generation/evaluation use OpenAI. RAGAS metadata records evaluator `gpt-4o-mini` and `text-embedding-3-small`.
- [x] Start Qdrant using `infra/docker-compose.yml` (pinned image `qdrant/qdrant:v1.9.7`) and confirm it is healthy on port 6333 (Compose service `infra-qdrant-1` is running; `http://localhost:6333/healthz` returned HTTP 200 on 2026-10-12).
- [x] Restore and adapt the five previous-lab modules in `src/`: `m1_chunking.py`, `m2_search.py`, `m3_rerank.py`, `m4_eval.py`, `m5_enrichment.py`. Source: `hmster915/K4-Track3A-Day18-Production-RAG`; interfaces match `doc/PIPELINE_INTERFACE.md`, and setup does not call `pipeline.py`. Syntax/import and live integration checks passed.
- [x] Add `OPENAI_API_KEY` to the project-local, ignored `.env`; the live setup loaded it successfully. Never commit or share it, and keep `.env.example` free of secret values.
- [x] Member 1 ran `python scripts/setup_answers.py --live` (2026-10-12): 116 chunks indexed in Qdrant and 50 answers generated in their verified environment.
- [x] Verify `artifacts/answers_50q.json`: exactly 50 source IDs in source order; 20 factual, 20 multi_hop, 10 adversarial; source questions and ground truth unchanged; all answers and retrieved contexts are non-empty.
- [x] Verify generation provenance for all answers: `generation_mode=llm`; all rows include model ID `gpt-4o-mini-2024-07-18`. No extractive fallback rows.
- [x] Fill team Skynet, shared repo, both members/MSSVs/roles, leader/co-submitters and integration/submission-link owner in `doc/TEAM.md`; deadline remains explicitly pending coach confirmation.

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
- [x] Run `.venv\Scripts\python.exe scripts\run_experiments.py --phase b --live`; after merging the updated Member 1 answers, reran Phase B at `2026-10-12T16:19:49.416906+00:00` so candidate A matches the saved answers.
- [x] Refresh `doc/reports/bias_report.md` from the final judge artifact with five pair records, ten calibration rows, κ/agreement, updated position/verbosity measures and limitations.

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

- [x] Complete every member’s real role, evidence, checks, learning, limitations and AI/source disclosure in `doc/TEAM.md`; identify unresolved deadline as pending coach confirmation.
- [x] Complete all three reports from actual artifacts; report contract validation passes with no placeholders or blank required tables.
- [x] Run `.venv\Scripts\python.exe scripts\check_lab.py` from the repo root after the latest TEAM update — 24/24 checks pass; this is a completeness checker, not a rubric score.
- [x] Re-ran Phase B once because the merged Member 1 branch replaced 37 answer texts and all 50 contexts; this restored source consistency. Phase C final artifact remains valid, and no further live runs are planned.
- [x] Secret/data review: committed-file scan found no API-key-shaped value; `.env`, `.venv`, caches and installers are not tracked. Fixture PII is synthetic; TEAM contains the teammate identity they supplied for submission.
- [x] Scan committed Git content for API-key-shaped values: none found; `.env` is not tracked. All four experiment artifacts are tracked and not ignored.
- [x] Merge PR #1 (`chiến` → `main`) with all Member 1 changes; local merge commit `f1b2239` was pushed and pulled back from `origin/main`. GitHub reports the PR merged.
- [x] Offline suite after integration: `.venv\Scripts\python.exe -m pytest tests\ -m "not integration" -q --tb=short` — 94 passed, 3 deselected. `pip check` passes; NumPy 1.26.4, PyArrow 17.0.0 and SentencePiece 0.2.2 verified.
- [x] Verify all experiment artifacts are committed and not ignored; `answers_50q.json`, `ragas_50q.json`, `judge_results.json` and `guard_results.json` are tracked on the merged main.
- [x] Verify pushed main: clean working tree; local and remote HEAD both `f1b2239ff39e34c3e3e2b8f9cfe7f12bad6d46f0`.
- [ ] Push the completed CP4 documentation, record/verify the submission commit, confirm graders can access the repo, and have the two co-submitters submit one link through the announced VLearn/coach channel.
- [ ] Confirm the lab date and applicable deadline from the coach announcement. The docs default to 23:59 on lab day, Asia/Ho_Chi_Minh.

## Scoring reminders

- Required 100 points: Phase A 30, Phase B 35, Phase C 35. Bonus up to 10: adversarial mean below factual +4; κ >0.6 on the correct ten answers +3; at least 18/20 attacks with 8/8 clean allowed +3.
- Mock tests do not replace live artifacts. Never invent scores, labels, model provenance, latency or execution claims.
- One shared team repository is submitted by the team lead. Individual contribution is documented in TEAM and Git history; follow the coach’s AI-use and late-submission rules.

## Suggested two-person work split

Replace Member 1/Member 2 with actual names in `doc/TEAM.md`. Keep one shared repository and review each other’s results before live runs and submission.

Current assignment confirmed by the user: Phùng Trọng Chiến (2A202602430) owns Member 1; Nguyễn Hồng Khoa (2A202602534) owns Member 2. Team Skynet has two co-submitters; Khoa integrates and prepares/submits the repository link with Chiến.

### Member 1 — RAG preparation and Phase A

- [x] Own the five RAG modules (`m1`–`m5`) and verify their contracts against `doc/PIPELINE_INTERFACE.md`.
- [ ] Coordinate with Member 2 to confirm environment, Qdrant, models and local API configuration are ready; do not expose the key.
- [x] Build and run `artifacts/answers_50q.json`; verify 50 IDs, distribution counts, contexts, references and generation provenance.
- [x] Implement and own Phase A Tasks 1–4 in `src/phase_a_ragas.py`; run offline tests and the live Phase A experiment.
- [x] Own `doc/reports/failure_clusters.md`, grounding analysis in the saved JSON and source contexts.
- [x] Give Member 2 the verified answers artifact and record module/setup/Phase A contributions in TEAM.

### Member 2 — Environment, Phase B/C and integration

- [ ] Own full runtime dependency installation/import checks, compiler visibility, model download checks and Qdrant startup; record actual results in TEAM.
- [x] Implement and own Phase B Tasks 5–8 in `src/phase_b_judge.py`; rerun offline validation and live Phase B after the merged answer handoff.
- [x] Own `doc/reports/bias_report.md`, using the exact pair sources and supplied `model_answer` calibration data.
- [x] Implement and own Phase C Tasks 9a–12 in `src/phase_c_guard.py`; run offline tests and final live Phase C experiment.
- [x] Own `doc/reports/blueprint.md`, keeping measured results distinct from proposals and unmeasured latency scopes.
- [ ] Coordinate the final checker, secret/artifact review, commit SHA, and submission handoff with the team lead; record actual work in TEAM.

### Shared handoffs and review gates

- [ ] Member 2 confirms CP0 environment readiness before Member 1 runs live answer generation.
- [ ] Member 1 reviews answer counts, IDs, contexts and generation metadata before Member 2 starts Phase B; both review before Phase A/B/C live runs to avoid paid reruns.
- [ ] Each owner gives the other person the exact run command, artifact path and observed result; the reviewer reconciles the report against the artifact.
- [ ] Both members complete their own `INDIVIDUAL` entry and verify the final repo/checker output before the team lead submits one link.
