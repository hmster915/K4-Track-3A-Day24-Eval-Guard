# Nhóm thực hiện K4 Track 3A

Tên nhóm: {{Tên nhóm}}

Repo chung: https://github.com/hmster915/K4-Track-3A-Day24-Eval-Guard

Trưởng nhóm/người nộp: {{Họ tên và MSSV}}

Ngày lab/deadline áp dụng: {{Ngày giờ theo thông báo lớp}} — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: {{Commit SHA}}

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Phùng Trọng Chiến | 2A202602430 | Member 1: module RAG m1–m5, sinh 50 answers, Phase A Tasks 1–4 và phân tích lỗi | Nhánh `chiến`; `src/m1_chunking.py` đến `src/m5_enrichment.py`, `src/phase_a_ragas.py`, `tests/test_member1_modules.py`, `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`, `doc/reports/failure_clusters.md` |
| 2 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |

Người tích hợp/chạy batch/nộp link: {{Họ tên, công việc và bằng chứng}}.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: {{Phiên bản thực tế}}.
Virtualenv/dependencies/imports: {{Lệnh và kết quả}}.
Models/Qdrant/50 answers đã chuẩn bị: {{Bằng chứng và giới hạn/fallback}}.
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

### {{HoVaTen}}-{{MSSV}}

- Phần được giao và phần thực tế đã làm: {{Nhiệm vụ, file/hàm, mục đích}}.
- Bằng chứng: {{Commit/PR và artifacts/reports liên quan}}.
- Cách kiểm tra: {{Unit mock hoặc live experiment, lệnh và kết quả}}.
- Điều đã học: {{Khái niệm và cách thể hiện trong bài}}.
- Giới hạn/cách xử lý: {{Vấn đề và kiểm chứng}}.
- Nguồn/AI hỗ trợ nếu có: {{Công cụ, phạm vi, cách tự kiểm chứng}}.

## Cập nhật sau khi nộp

{{Ghi phiên bản nộp; nếu sửa sau deadline, ghi commit/thời điểm/lý do và thông báo
coach cho phép áp dụng bản cập nhật. Nếu không có cập nhật, ghi rõ không có.}}
