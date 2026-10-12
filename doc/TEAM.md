# Nhóm thực hiện K4 Track 3A

Tên nhóm: Skynet

Repo chung: https://github.com/hmster915/K4-Track-3A-Day24-Eval-Guard

Trưởng nhóm: Nguyễn Hồng Khoa (2A202602534). Người đồng nộp: Nguyễn Hồng Khoa (2A202602534) và Phùng Trọng Chiến (2A202602430).

Ngày lab/deadline áp dụng: Chưa có thông tin deadline từ thông báo coach; nhóm cần đối chiếu trước khi nộp — Asia/Ho_Chi_Minh (UTC+07:00).

Mốc CP4 đã push có đầy đủ thông tin nhóm và bộ artifacts/báo cáo để đối chiếu: `3605c713ac58dcda25b7ac5a1df9c3b23b28fca2`. Các cập nhật nhận diện báo cáo và checklist tiếp theo được lưu trên `main`.

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Phùng Trọng Chiến | 2A202602430 | Member 1: module RAG m1–m5, sinh 50 answers, Phase A Tasks 1–4 và phân tích lỗi | Nhánh `chiến`; `src/m1_chunking.py` đến `src/m5_enrichment.py`, `src/phase_a_ragas.py`, `tests/test_member1_modules.py`, `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`, `doc/reports/failure_clusters.md` |
| 2 | Nguyễn Hồng Khoa | 2A202602534 | Member 2: Phase B/C, judge/guard reports, final integration | Commits `f212848`, `367f484`, `98490fe`, merge `f1b2239`; `artifacts/judge_results.json`, `artifacts/guard_results.json`, `doc/reports/bias_report.md`, `doc/reports/blueprint.md` |

Người tích hợp/chạy batch/nộp link: Nguyễn Hồng Khoa (2A202602534) tích hợp, chạy kiểm tra batch và chuẩn bị/nộp link repo cùng Phùng Trọng Chiến (2A202602430).

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 11 Pro; project `.venv` Python 3.11.9; MSVC 14.51 / compiler 19.51.36260.
Virtualenv/dependencies/imports: `.venv\Scripts\python.exe -m pip check` không có dependency lỗi; NumPy 1.26.4, PyArrow 17.0.0, SentencePiece 0.2.2; lab imports và offline tests đã kiểm tra.
Models/Qdrant/50 answers đã chuẩn bị: Member 1 ghi nhận Qdrant 1.9.7, collection `lab24_production` có 116 chunks; retrieval dùng BGE-M3 và BGE reranker v2-m3 đã tải/kiểm tra trong môi trường Member 1. Generation dùng OpenAI `gpt-4o-mini-2024-07-18`; `artifacts/answers_50q.json` có 50 câu theo 20/20/10, không fallback. Project `.env` chứa key nhưng không được commit.
Nếu cài full NeMo chưa thành công, ghi lỗi thực tế; không dùng unit test pass
hoặc pip resolve để khẳng định runtime đã chạy.

## INDIVIDUAL

Sao chép mẫu cho mỗi thành viên; tiêu đề họ tên không dấu-MSSV.

### PhungTrongChien-2A202602430

- Phần được giao: RAG modules and answers, Phase A, failure analysis report.
- Phần mã đã làm: `m1` đọc Markdown trong Day24 và chunk theo mục; `m5` thêm metadata nguồn/phiên bản; `m2` BM25 tiếng Việt + BGE-M3/Qdrant + RRF; `m3` cross-encoder rerank; `m4` gọi bốn metric RAGAS thật và ghi model evaluator; Tasks 1–4 giữ đúng nguồn, thứ tự, bottom 10 và nhóm yếu theo mean.
- Bằng chứng: mã trong `src/`, `tests/test_member1_modules.py`, `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`, `doc/reports/failure_clusters.md` và commit triển khai Member 1 trên nhánh `chiến` (xem lịch sử nhánh và PR). Mọi module chạy độc lập trong Day24, không import các repo day khác.
- Kiểm tra offline: `python -m pytest tests/test_member1_modules.py tests/test_phase_a.py tests/test_support.py tests/test_report_contracts.py -q --tb=short --basetemp=.venv/pytest-member1-complete`: 74 passed. Tests dùng mock.
- Kiểm tra live: `python scripts/setup_answers.py --live` tạo đủ 50 answers (20/20/10), toàn bộ mode `llm`, model `gpt-4o-mini-2024-07-18`, không extractive fallback; chạy queries mất 596,3 giây. `python scripts/run_experiments.py --phase a --live` đo đủ 200 metric hữu hạn, lưu report lúc 12/10/2026 22:29:49 UTC+07:00. Mean factual=0,8327; multi_hop=0,7079; adversarial=0,7641. JSON Schema, nguồn và source SHA-256 được đối chiếu; báo cáo phân tích đủ bottom 10, matrix và các trường hợp đại diện.
- Môi trường cá nhân: Windows 11 Pro, Python 3.11.15 trong `.venv`, PyTorch CPU; lượt chạy dùng OMP_NUM_THREADS=4 và MKL_NUM_THREADS=4. `pip check` không có dependency lỗi. Qdrant 1.9.7 phản hồi tại localhost:6333, collection `lab24_production` có 116 points từ 25 tài liệu. BGE-M3 và BGE reranker v2-m3 đã tải, kiểm tra SHA-256 và chạy model thật; evaluator `gpt-4o-mini` + `text-embedding-3-small`.
- Phân tích: matrix worst_metric thống kê metric thấp nhất của từng câu; distribution yếu được xác định theo mean thấp nhất. Báo cáo đối chiếu answer, contexts và reference để phân loại nguyên nhân. Model generation và evaluator được ghi riêng.
- Giới hạn/cách xử lý: evaluator dùng RAGAS, dừng khi model/retrieval lỗi. Khóa PyArrow 17 để tương thích NumPy 1.26.4 và thêm SentencePiece cho tokenizer reranker. Ba answers abstain dù có một phần hoặc đủ bằng chứng; câu multi-hop thiếu coverage top 3; một số phép tính đúng bị faithfulness chấm 0. Các trường hợp này được phân tích trong failure report.

### NguyenHongKhoa-2A202602534

- Phần được giao và phần thực tế đã làm: Member 2 phụ trách Phase B/C và tích hợp. Hoàn thiện judge pairwise/calibration, Presidio/NeMo rails, adversarial suite, output check và latency sampling; cập nhật bias report và blueprint.
- Bằng chứng: commits `f212848` (CP2), `367f484` (CP3 implementation), `98490fe` (CP3 live), merge `f1b2239`; artifacts `judge_results.json`, `guard_results.json`; reports `bias_report.md`, `blueprint.md`.
- Cách kiểm tra: sau khi nhận answers mới từ PR Member 1, chạy lại `.venv\Scripts\python.exe scripts\run_experiments.py --phase b --live` (timestamp `2026-10-12T16:19:49.416906+00:00`); Phase C live cuối có 20/20 attack, 8/8 clean và 4/4 outputs đúng. `.venv\Scripts\python.exe -m pytest tests\ -m "not integration" -q --tb=short`: 94 passed, 3 deselected. Checker qua các artifact/report checks; CP4 checker được chạy lại sau khi hoàn tất thông tin nhóm.
- Điều đã học: đảo thứ tự A/B giúp nhận biết bất ổn của judge; guard phải đánh giá attack cùng clean controls; latency cần đo từng tầng và báo P95 thật. Batch hiện tại đạt 20/20 attack và 0 false positives; input guard P95 931.35081 ms vượt budget 500 ms.
- Giới hạn/cách xử lý: Phase B/C là tập mẫu nhỏ; RAG, output và full-request latency chưa đo. Đã rerun Phase B sau khi CP1 thay đổi 37 answers và contexts để candidate A khớp artifact mới. CI/CD trong blueprint là đề xuất, chưa triển khai.
- Nguồn/AI hỗ trợ nếu có: OpenAI Codex hỗ trợ triển khai/sửa code và soạn báo cáo trong phạm vi Member 2; tự kiểm chứng bằng offline suite, live artifacts, schema/report contracts và checker. Không ghi API key vào repo.

## Cập nhật sau khi nộp

Chưa nộp; phiên bản và thời điểm nộp sẽ được ghi sau khi team nộp link. Chưa có xác nhận về deadline từ thông báo coach.
