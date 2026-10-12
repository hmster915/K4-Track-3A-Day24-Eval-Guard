# Blueprint CI/CD cho RAG và guardrails

Nhóm: Chưa được cung cấp trong workspace.

Phụ trách báo cáo: Member 2.

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: `artifacts/ragas_50q.json`, `artifacts/judge_results.json` và
`artifacts/guard_results.json`; các batch live hoàn tất ngày 2026-10-12. Run
Phase C được báo cáo có timestamp `2026-10-12T16:08:15.202430+00:00`, model
guard `gpt-4o-mini`. Hai batch C trước đó dùng để hiệu chỉnh input prompt; artifact
hiện tại là batch cuối sau hiệu chỉnh.

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

Phase C live tạo 20 timed samples sau hai warm-up thật, không short-circuit, dùng
percentile nội suy tuyến tính. Tổng mỗi sample bằng thời gian Presidio cộng thời
gian NeMo input trên cùng sample.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---:|---:|---:|---|
| Presidio | 0.235 | 0.410 | 0.422 | Đo trong Phase C live |
| NeMo input | 711.926 | 931.066 | 948.012 | Đo trong Phase C live |
| Input guard sequential | 712.257 | 931.350 | 948.408 | Đo trong Phase C live |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi Task 12 |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi Task 12 |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input guard |

Input-layer budget target là 500 ms; `latency_budget_ok=false` vì input guard P95
931.35081 ms vượt budget. NeMo input là bottleneck trong phép đo này; Presidio
P95 là 0.409605 ms. Các số là từ một batch 20 samples với model/API đang dùng,
nên biến động mạng và tải dịch vụ có thể ảnh hưởng kết quả. RAG, NeMo output và
full request vẫn chưa đo.

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

Phase C live cuối đạt 20/20 attack blocked, 8/8 clean allowed (false-positive
rate 0), và 4/4 output cases đúng. Kết quả này đạt cả ngưỡng lab 15/20 lẫn mục
tiêu bonus 18/20 với clean controls đạt. Các batch hiệu chỉnh trước đó từng chặn
nhầm câu hỏi mật khẩu/VPN; prompt được làm rõ bằng các ví dụ policy đó trước batch
cuối.

Kết quả Phase A: `avg_score` factual 0.8271, multi-hop 0.6585,
adversarial 0.6581; adversarial thấp nhất với chênh lệch chỉ 0.0004 so với
multi-hop. `answer_relevancy` là worst metric của 27/50 câu. Phase B có Cohen’s
κ = 1.000 trên 10 nhãn; position inconsistency 2/5 và verbosity win rate 3/3
trên các case decisive. Các mẫu nhỏ này chỉ mô tả fixtures hiện tại, không
chứng minh chất lượng tổng quát. Phase C chỉ đo fixtures 20 attack, 8 clean,
4 output; không chứng minh khả năng chặn trên phân phối yêu cầu production.

Các cải tiến có thể kiểm thử:

1. Sửa prompt abstain để trả lời khi contexts chứa bằng chứng; so sánh answer
   relevancy và faithfulness trước/sau trên cùng 50 câu.
2. Giữ câu phủ định trong cùng chunk và kiểm tra truy vấn bảo hiểm PVI; so sánh
   context recall cùng câu trả lời trước/sau.
3. Ưu tiên policy version hiện hành khi truy xuất xung đột; kiểm tra các câu
   password v1/v2 và VPN trên regression set.
4. Bổ sung cặp judge cân bằng độ dài và nội dung đúng/sai; đo lại position
   inconsistency và verbosity win rate trước khi kết luận bias.
5. Giảm độ trễ NeMo input bằng cách benchmark model/provider và cấu hình rail
   theo cùng 20 mẫu; yêu cầu giữ nguyên 20/20 attack và 8/8 clean trước khi chọn
   cấu hình nhanh hơn.
