# Phân tích lỗi Phase A

Người phụ trách: **Phùng Trọng Chiến — 2A202602430 (Member 1)**.

Repo nhóm: https://github.com/hmster915/K4-Track-3A-Day24-Eval-Guard. Nhóm có hai thành viên; báo cáo này thuộc phần Member 1.

Nguồn: [ragas_50q.json](../../artifacts/ragas_50q.json), timestamp `2026-10-12T15:29:49.597111+00:00` (UTC), tương ứng **12/10/2026 22:29:49 UTC+07:00**. Answers: [answers_50q.json](../../artifacts/answers_50q.json).

## Phạm vi và điều kiện chạy

25 tài liệu Markdown trong `data/` → tìm tiêu đề mục → đọc tới tiêu đề tiếp theo → chia parent tối đa 2048 ký tự, child tối đa 256 ký tự → thêm nguồn/tiêu đề/phiên bản/mục từ corpus → 116 chunks → BM25 tiếng Việt + dense BGE-M3 trên Qdrant → RRF top 20 → cross-encoder top 3 → generation → bốn metric RAGAS trên 50 câu.

Windows 11 Pro, Python 3.11.15, PyTorch CPU; lượt chạy dùng OMP_NUM_THREADS=4 và MKL_NUM_THREADS=4. Qdrant 1.9.7, collection `lab24_production`, 116 points. Enrichment chỉ thêm metadata từ tài liệu; không sinh fact hay gọi LLM. Mọi module nằm độc lập trong Day24.

Generation: **50/50 `llm`**, model `gpt-4o-mini-2024-07-18`; **0 extractive fallback**. IDs 9, 39, 50 có answer “Không tìm thấy.”: đây là abstention do LLM tạo, không phải fallback. Giữ nguyên các answers này khi evaluation.

Evaluator RAGAS 0.1.22: `gpt-4o-mini` và `text-embedding-3-small`, cấu hình trực tiếp trong m4 và chuyển `metadata.evaluator_models` sang Phase A. Alias evaluator không khẳng định snapshot provider đã resolve. Retrieval dùng `BAAI/bge-m3` (1024 chiều); rerank dùng `BAAI/bge-reranker-v2-m3`. Judge/guard không tham gia lượt A.

Giữ nguyên question/distribution/ground_truth của fixture và policy cũ/mới. Generation chỉ nhận question và contexts. Không dùng ground truth làm answer; không dùng lexical proxy hoặc thay NaN bằng điểm giả. Cả 200 giá trị metric đều hữu hạn trong [0,1].

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---:|---:|---:|
| faithfulness | 0.9125 | 0.5464 | 0.8667 |
| answer_relevancy | 0.4934 | 0.4643 | 0.5232 |
| context_precision | 0.9750 | 0.9750 | 0.9833 |
| context_recall | 0.9500 | 0.8458 | 0.6833 |
| avg_score | 0.8327 | 0.7079 | 0.7641 |

Số hiển thị làm tròn bốn chữ số; phép tính và đối chiếu dùng giá trị đầy đủ trong JSON.

## Bottom 10 — nguyên văn đầu ra Task 3

| Rank | ID | Distribution | Question | Avg score | Worst metric | Diagnosis | Suggested fix |
|---:|---:|---|---|---:|---|---|---|
| 1 | 39 | multi_hop | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | 0.2500 | faithfulness | Có thể có khẳng định thiếu căn cứ; đối chiếu answer với contexts | Yêu cầu dẫn nguồn và từ chối khi context thiếu bằng chứng |
| 2 | 50 | adversarial | Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không? | 0.4167 | faithfulness | Có thể có khẳng định thiếu căn cứ; đối chiếu answer với contexts | Yêu cầu dẫn nguồn và từ chối khi context thiếu bằng chứng |
| 3 | 9 | factual | Nam nhân viên được nghỉ bao nhiêu ngày khi vợ sinh con? | 0.5000 | faithfulness | Có thể có khẳng định thiếu căn cứ; đối chiếu answer với contexts | Yêu cầu dẫn nguồn và từ chối khi context thiếu bằng chứng |
| 4 | 31 | multi_hop | Nhân viên đi công tác trong nước, ở khách sạn 2 đêm với giá 1.500.000 VNĐ/đêm. Công ty thanh toán tối đa bao nhiêu cho tiền khách sạn? | 0.5389 | faithfulness | Có thể có khẳng định thiếu căn cứ; đối chiếu answer với contexts | Yêu cầu dẫn nguồn và từ chối khi context thiếu bằng chứng |
| 5 | 7 | factual | Nghỉ phép không lương 20 ngày cần ai phê duyệt? | 0.5684 | answer_relevancy | Có thể answer chưa trực tiếp đáp ứng câu hỏi | Kiểm tra câu hỏi/answer và yêu cầu trả lời đủ từng ý được hỏi |
| 6 | 26 | multi_hop | Nhân viên vừa kết hôn và cùng tuần đó có con kết hôn. Tổng số ngày nghỉ đặc biệt có lương là bao nhiêu? | 0.5738 | faithfulness | Có thể có khẳng định thiếu căn cứ; đối chiếu answer với contexts | Yêu cầu dẫn nguồn và từ chối khi context thiếu bằng chứng |
| 7 | 49 | adversarial | Theo chính sách nghỉ phép cũ (v2023), nhân viên được nghỉ bao nhiêu ngày? Còn chính sách nào đang có hiệu lực hiện tại? | 0.6210 | context_recall | Có thể thiếu ý cần thiết; đối chiếu contexts với reference | Kiểm tra ranh giới chunk và mở rộng retrieval cho câu nhiều bước |
| 8 | 24 | multi_hop | Nhân viên tạm ứng 15 triệu, sau 20 ngày mới thanh toán. Bị phạt bao nhiêu? | 0.6227 | faithfulness | Có thể có khẳng định thiếu căn cứ; đối chiếu answer với contexts | Yêu cầu dẫn nguồn và từ chối khi context thiếu bằng chứng |
| 9 | 34 | multi_hop | Nhân viên tạm ứng 4 triệu và một nhân viên khác tạm ứng 7 triệu: quy trình phê duyệt khác nhau thế nào? | 0.6792 | answer_relevancy | Có thể answer chưa trực tiếp đáp ứng câu hỏi | Kiểm tra câu hỏi/answer và yêu cầu trả lời đủ từng ý được hỏi |
| 10 | 33 | multi_hop | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | 0.6884 | answer_relevancy | Có thể answer chưa trực tiếp đáp ứng câu hỏi | Kiểm tra câu hỏi/answer và yêu cầu trả lời đủ từng ý được hỏi |

Diagnosis/fix trong bảng giữ đúng từ Task 3. Đây là dấu hiệu cần kiểm tra; kết luận bên dưới dựa thêm trên answer, contexts và reference của từng ID.

## Đối chiếu bằng chứng và nguyên nhân

### 1. Từ chối dù có căn cứ — ID 9 và 50

**ID 9:** answer “Không tìm thấy.”, faithfulness=0, relevancy=0, recall=1. Context đầu có “Sinh con (nam giới): 5 ngày làm việc liên tục” và quy định không trừ phép năm, khớp reference. Mốc nguồn: [nghi_phep_dac_biet.md](../../data/nghi_phep_dac_biet.md), mục “Các trường hợp được nghỉ phép đặc biệt”, dòng 5–8. Đây là lỗi generation/abstention quá mức; thiếu retrieval không giải thích được trường hợp này.

**ID 50:** answer cũng là “Không tìm thấy.”. Context thứ hai có lệnh cấm VPN cá nhân (NordVPN, ExpressVPN) trong mạng công ty; context đầu yêu cầu VPN khi WFH. Mốc: [vpn_truy_cap.md](../../data/vpn_truy_cap.md), “Quy định sử dụng”, và [lam_viec_tu_xa.md](../../data/lam_viec_tu_xa.md), “Yêu cầu kỹ thuật”. Reference yêu cầu KHÔNG và dùng VPN công ty. Căn cứ để bác VPN cá nhân đã được retrieve nhưng không dùng để trả lời. Context còn thiếu phần xác định WireGuard nên recall=0,6667: có cả lỗi generation và thiếu một ý retrieval. Abstention không chứng minh đã nhận ra bẫy phủ định.

**Đề xuất:** trả lời trực tiếp và trích căn cứ; chỉ abstain đối với ý thật sự thiếu. Với câu nhiều phần, trả lời phần đủ bằng chứng và nêu phần còn thiếu. Kiểm tra lại IDs 9/50 và các câu có đủ căn cứ trước khi mở rộng batch.

### 2. Top 3 thiếu coverage — ID 39 và 33

**ID 39:** contexts gồm độ dài v1 (8 ký tự), chu kỳ v1 (90 ngày) và MFA v2. Thiếu độ dài v2 (12 ký tự), chu kỳ v2 (120 ngày), lưu ý MFA v1; answer “Không tìm thấy.”. Mốc còn thiếu: [mat_khau_v2.md](../../data/mat_khau_v2.md), “Yêu cầu mật khẩu” dòng 5, “Chu kỳ thay đổi” dòng 11; [mat_khau_v1.md](../../data/mat_khau_v1.md), “Lưu ý”. Reference yêu cầu đủ hai phiên bản × ba thuộc tính. Recall=0,5 có bằng chứng thiếu coverage; generation đồng thời bỏ các ý đã có. Precision=0,5 là số judge đo, không đủ để kết luận mọi chunk v1 sai vì câu hỏi có yêu cầu v1.

**ID 33:** contexts có phép cơ bản 15 ngày, thêm 1 ngày/3 năm và điện thoại Manager 500.000. Answer tính đúng **19 ngày phép** nhưng gọi **500.000** là tổng phụ cấp. Reference yêu cầu **1.500.000 = 1.000.000 ăn trưa + 500.000 điện thoại**. Mốc bị bỏ: [phu_cap.md](../../data/phu_cap.md), “Phụ cấp ăn trưa” dòng 5. Top 3 dùng hai slots cho phép năm và một cho điện thoại nên thiếu ăn trưa. Đây là lỗi retrieval coverage và generation kết luận “tổng” từ dữ liệu chưa đủ; recall=0,5.

**Đề xuất:** giữ child để tìm mốc, rồi mở rộng parent/các mục cần thiết trước generation. Câu so sánh phiên bản phải giữ các nguồn được hỏi và đủ thuộc tính; không lọc toàn bộ bản cũ. Thử coverage trên IDs 33/39 rồi so điểm và số contexts, tránh chỉ tăng top-k và thêm nhiễu.

### 3. Phép tính đúng nhưng faithfulness thấp — ID 24, 26, 31

**ID 24:** answer **50.000 VNĐ = 2% × 15.000.000 × 5/30**, khớp reference. Contexts đủ hạn hoàn ứng 15 ngày và công thức pro-rata trong [tam_ung.md](../../data/tam_ung.md), “Thời hạn thanh toán” dòng 8, “Phạt quá hạn” dòng 11–13. Recall=1 nhưng faithfulness=0. Không đủ căn cứ để chỉ từ metric 0 kết luận phép tính là hallucination.

**ID 26:** answer **4 ngày = 3 ngày kết hôn + 1 ngày con kết hôn**, khớp số ngày trong reference. Context đầu có hai số tại [nghi_phep_dac_biet.md](../../data/nghi_phep_dac_biet.md), dòng 6 và 9; đoạn cuối bị cắt ở “1 ngày làm” nhưng vẫn giữ số 1. Recall=1, faithfulness=0. Answer chưa nói rõ “không trừ phép năm”; phân biệt thiếu diễn giải với sai tổng số ngày.

**ID 31:** answer **2.400.000 = 1.200.000/đêm × 2 đêm**, đúng reference và trần khách sạn trong [cong_tac_phi.md](../../data/cong_tac_phi.md), “Công tác trong nước” dòng 6. Chưa giải thích phần vượt trần do nhân viên chịu. Số đêm và giá thực tế đến từ question, không nằm trong policy context. Faithfulness=0; recall=0,6667.

Trong RAGAS 0.1.22, Faithfulness tách statements từ question/answer nhưng bước NLI `_create_nli_prompt` chỉ gửi contexts và statements. Dữ kiện tình huống/tổng tính toán không ghi nguyên văn trong policy có thể bị judge coi là thiếu căn cứ. Đây là **giả thuyết về giới hạn evaluator**, phù hợp với ba đối chiếu trên; lượt này chưa lưu từng NLI verdict nên chưa chứng minh nguyên nhân riêng của từng điểm 0. Giữ nguyên điểm đã đo.

**Đề xuất:** bổ sung kiểm tra công thức độc lập và review người. Nếu thử evaluator có question-premise, ghi thành phép đo mới, không thay scores baseline. Generation nên tách dữ kiện câu hỏi, quy tắc policy, phép tính và kết luận, có dẫn nguồn cho quy tắc.

### 4. Trả lời đúng ý hỏi nhưng reference có thêm ý — ID 7, 34, 49

**ID 7:** question hỏi ai phê duyệt 20 ngày không lương; answer CEO đúng mốc 16–30 ngày tại [nghi_phep_khong_luong.md](../../data/nghi_phep_khong_luong.md), “Quy trình phê duyệt” dòng 8. Reference còn yêu cầu tự đóng bảo hiểm khi nghỉ trên 14 ngày (dòng 11), nhưng mục này không được retrieve. Recall=0,5 và relevancy=0,2734 không chứng minh chọn sai người phê duyệt.

**ID 34:** answer phân biệt đúng 4 triệu cần trưởng phòng và 7 triệu cần thêm kế toán trưởng, khớp [tam_ung.md](../../data/tam_ung.md), “Phê duyệt”. Reference thêm hạn hoàn ứng 15 ngày; context/answer thiếu ý này. Recall=0,6667, relevancy=0,3834. Phân biệt thiếu coverage so với reference đầy đủ với sai ý question thực sự hỏi.

**ID 49:** answer đúng **v2023: 12 ngày**, **v2024 hiện hành: 15 ngày**. Contexts có cả hai phiên bản và thâm niên v2023, nhưng thiếu thâm niên v2024 (1 ngày/3 năm) mà reference yêu cầu. Mốc: [nghi_phep_nam_v2024.md](../../data/nghi_phep_nam_v2024.md), dòng 8; [nghi_phep_nam_v2023.md](../../data/nghi_phep_nam_v2023.md), dòng 8. Recall=0,3333 không đồng nghĩa dùng nhầm bản hiện hành; answer này đã nhận biết đúng phiên bản.

**Đề xuất:** review các ý bắt buộc và bổ sung trong question/reference; giữ fixture gốc khi chấm lab. Bộ eval mới nên tách accuracy trên ý hỏi và reference coverage. AnswerRelevancy sinh ba câu hỏi từ answer rồi tính cosine với câu hỏi gốc, kèm cờ noncommittal; điểm thấp cần đọc cùng nội dung, không tự là bằng chứng lỗi nghiệp vụ.

## Matrix và nhóm yếu nhất

| Worst metric | factual | multi_hop | adversarial | Total |
|---|---:|---:|---:|---:|
| faithfulness | 2 | 10 | 1 | 13 |
| answer_relevancy | 17 | 9 | 6 | 32 |
| context_precision | 0 | 0 | 0 | 0 |
| context_recall | 1 | 1 | 3 | 5 |

Tổng mỗi cột là **20/20/10** vì mỗi câu đếm một lần theo metric thấp nhất. Không định nghĩa tất cả 50 câu là failures. Tie theo thứ tự faithfulness → answer_relevancy → context_precision → context_recall.

Nhóm yếu nhất theo mean: **multi_hop = 0,7079**. Worst metric phổ biến nhất: **answer_relevancy, 32/50 câu**. Trong multi-hop, faithfulness là worst ở **10/20 câu**; mean faithfulness=0,5464, thấp hơn factual=0,9125. Bottom 10 có 6 multi-hop, 2 factual, 2 adversarial.

Bằng chứng gồm thiếu ý khi top 3 phủ nhiều mục/nguồn (33,39), cùng giới hạn judge với phép tính từ dữ kiện tình huống (24,26,31). Context_precision cao không đảm bảo đủ context hay answer đúng. Không dùng tổng cột để chọn nhóm yếu.

## Bẫy adversarial và giới hạn

Adversarial mean **0,7641 < factual 0,8327**, nhưng cao hơn multi-hop. Chênh lệch không tự chứng minh nhận ra bẫy. ID 49 nhận biết đúng phiên bản nhưng thiếu coverage; ID 50 không trả lời lệnh cấm dù có căn cứ. Các bản phép năm v2023/v2024 và mật khẩu v1/v2 đều được giữ.

Chỉ có 50 câu, 10 adversarial; một lượt generation và một batch RAGAS, chưa có confidence interval hay baseline A/B. Generation dùng prompt starter, không đặt temperature riêng. Chunks theo ký tự có thể cắt câu/list; parents được tạo nhưng setup chỉ đưa children vào generation. Evaluator/prompt/embedding có thể gây khác biệt khi chạy lại; alias evaluator chưa cố định snapshot. Chưa đo riêng ảnh hưởng ngôn ngữ của các câu hỏi AnswerRelevancy sinh.

## Kiểm chứng và cách chạy lại

**74 tests offline pass**: Tasks 1–4, các module Member 1 và scaffold/contracts. Answers và Phase A đã validate JSON Schema, IDs, nguồn, metrics, bottom 10, matrix/means và source SHA-256. Các kết quả này không khẳng định đã hoàn thành Phase B/C.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_member1_modules.py tests/test_phase_a.py tests/test_support.py tests/test_report_contracts.py -q --tb=short --basetemp=.venv/pytest-member1-complete
.\.venv\Scripts\python.exe scripts/setup_answers.py --live
.\.venv\Scripts\python.exe scripts/run_experiments.py --phase a --live
```

Các lệnh `--live` dùng API. Khi thử cải tiến, lưu baseline hiện tại trước, thay một yếu tố mỗi lượt, so cùng 50 IDs; đối chiếu trước tiên 9/50 (abstention), 33/39 (coverage), 24/26/31 (calculation), 49 (version). Chỉ kết luận cải tiến từ answers/contexts/metrics mới chạy thật, không chỉnh số baseline.

Codex hỗ trợ mã, kiểm tra và đối chiếu báo cáo. Chủ phần việc cần đọc và giải thích lại kết quả trước khi nộp; Phase B/C và thông tin người còn lại thuộc phần tích hợp của nhóm.
