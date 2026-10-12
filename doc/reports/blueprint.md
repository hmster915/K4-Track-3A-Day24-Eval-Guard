# Blueprint CI/CD cho RAG và guardrails

Nhóm: Chưa được cung cấp trong workspace.

Phụ trách báo cáo: Member 2.

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả đã xác minh: `artifacts/ragas_50q.json` và
`artifacts/judge_results.json`, cả hai chạy ngày 2026-10-12. Phase C chưa có
artifact live: lần chạy ngày 2026-10-12 dừng khi OpenAI trả HTTP 429
`insufficient_quota`, nên không có số liệu guard/latency để báo cáo.

## Kiến trúc và failure action

Input → Presidio PII scan → NeMo input rail → RAG retrieval/generation → NeMo
output rail → response. Presidio chặn trước NeMo khi phát hiện CCCD/CMND, số
điện thoại Việt Nam hoặc email. NeMo dùng quyết định stop trong activated rail
log; không suy luận block từ câu chữ từ chối. Nếu bị chặn, trả phản hồi guard và
không tiếp tục RAG. Output bị rail chặn được thay bằng phản hồi an toàn; output
sạch được giữ nguyên.

Các quyết định production cần fail closed khi guard hoặc telemetry không khả
dụng, đồng thời không ghi raw PII/prompt nhạy cảm vào log. Chỉ lưu request ID,
nhãn loại PII, kết quả guard, thời gian từng tầng và model/version cần thiết để
điều tra. API key lấy từ secret store của môi trường chạy; không đưa vào mã,
artifact hoặc log. Đây là hướng dẫn triển khai, chưa có bằng chứng production.

## Phạm vi và số đo latency

Task 12 yêu cầu `input_layers_sequential`: đo Presidio và NeMo input liên tiếp,
không short-circuit; khởi tạo engine trước khi đo; chạy hai warm-up thật rồi bỏ
khỏi thống kê; dùng ít nhất 20 timed samples; tính percentile tuyến tính từ raw
samples và tính tổng guard từ tổng hai tầng trên từng sample.

Phase C live chưa chạy thành công vì quota API. Vì vậy hiện chưa có timed sample,
percentile hoặc đánh giá budget; không dùng số mock/offline làm số đo.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---:|---:|---:|---|
| Presidio | chưa đo | chưa đo | chưa đo | Chờ Phase C live |
| NeMo input | chưa đo | chưa đo | chưa đo | Chờ Phase C live |
| Input guard sequential | chưa đo | chưa đo | chưa đo | Chờ Phase C live |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi Task 12 |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi Task 12 |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input guard |

Input-layer budget target là 500 ms; `latency_budget_ok` chưa xác định do chưa có
live samples. Khi quota hoạt động, chạy đúng một batch Phase C với 20 samples,
giữ raw samples và đối chiếu thống kê trong `guard_results.json` trước khi kết
luận bottleneck.

## CI gates đề xuất

Các ngưỡng dưới đây là đề xuất, chưa có workflow CI/CD được triển khai:

- Trên cùng bộ 50 câu, chặn merge nếu RAGAS faithfulness dưới 0.75 hoặc
  `avg_score` dưới 0.65; lưu JSON để kiểm tra theo từng distribution.
- Với guard suite, yêu cầu ít nhất 18/20 attack bị chặn, 8/8 clean được cho qua,
  false-positive rate bằng 0 và cả bốn output cases đúng. Ngưỡng lab bắt buộc là
  15/20 attack cùng 8/8 clean; 18/20 là mục tiêu bonus.
- Chỉ áp dụng gate full-guard P95 dưới 500 ms sau khi pipeline có phép đo toàn
  request riêng. Không dùng input-layer P95 thay cho full-guard latency.
- Job CI chạy offline tests và checker trên artifact đã lưu; live API batch chỉ
  chạy theo lịch/dispatch có kiểm soát chi phí, quota và secret cấu hình. Runner
  phải trả nonzero nếu quality gates không đạt; kiểm tra hiện tại chưa tự enforce
  tất cả ngưỡng đề xuất.

## Monitoring và cải tiến

Theo dõi pass/block theo loại attack, clean false-positive rate, output rail
flagged rate, latency từng tầng, lỗi API/quota và model/config version. Cảnh báo
khi clean false positive lớn hơn 0, attack pass rate thấp hơn ngưỡng lab hoặc
latency p95 vượt 500 ms sau khi đã đo đúng scope. Khi có false positive, giữ
request ID và span đã redact để rà lại recognizer/rail; không lưu giá trị PII gốc.
Đánh giá drift bằng cùng fixtures phiên bản hóa và một tập kiểm tra mới được
review thủ công.

Kết quả hiện có từ Phase A: `avg_score` factual 0.8271, multi-hop 0.6585,
adversarial 0.6581; adversarial thấp nhất với chênh lệch chỉ 0.0004 so với
multi-hop. `answer_relevancy` là worst metric của 27/50 câu. Phase B có Cohen’s
κ = 1.000 trên 10 nhãn; position inconsistency 2/5 và verbosity win rate 3/3
trên các case decisive. Các mẫu nhỏ này chỉ mô tả fixtures hiện tại, không
chứng minh chất lượng tổng quát. Phase C hiện chưa có số attack/clean/output
hoặc latency live do lỗi quota nêu trên.

Các cải tiến có thể kiểm thử:

1. Sửa prompt abstain để trả lời khi contexts chứa bằng chứng; so sánh answer
   relevancy và faithfulness trước/sau trên cùng 50 câu.
2. Giữ câu phủ định trong cùng chunk và kiểm tra truy vấn bảo hiểm PVI; so sánh
   context recall cùng câu trả lời trước/sau.
3. Ưu tiên policy version hiện hành khi truy xuất xung đột; kiểm tra các câu
   password v1/v2 và VPN trên regression set.
4. Bổ sung cặp judge cân bằng độ dài và nội dung đúng/sai; đo lại position
   inconsistency và verbosity win rate trước khi kết luận bias.
5. Sau khi quota được khôi phục, chạy Phase C một lần, ghi artifact live, đối
   chiếu 20/8/4 kết quả và latency raw samples, rồi cập nhật các phần đang chờ.
