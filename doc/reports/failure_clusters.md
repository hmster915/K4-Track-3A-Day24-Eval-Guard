# Phân tích lỗi Phase A

Nhóm: Chưa ghi tên nhóm trong workspace.

Người phụ trách: Chưa được cung cấp.

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T14:33:33.652566+00:00.
Run live dùng 50 câu trả lời đã lưu; không có extractive fallback. Evaluator trả đủ 50 kết quả cho bốn metric.
Models generation: `gpt-4o-mini-2024-07-18`; evaluator từ metadata m4: `gpt-4o-mini`, `text-embedding-3-small`.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---:|---:|---:|
| faithfulness | 0.8833 | 0.4147 | 0.6000 |
| answer_relevancy | 0.5002 | 0.4402 | 0.3157 |
| context_precision | 1.0000 | 0.9417 | 1.0000 |
| context_recall | 0.9250 | 0.8375 | 0.7167 |
| avg_score | 0.8271 | 0.6585 | 0.6581 |

## Bottom 10 và nguyên nhân

Các trường diagnosis/fix dưới đây được giữ nguyên từ Task 3 trong artifact. Phần phân tích sau bảng kiểm tra answer, contexts và ground truth để làm rõ nguyên nhân theo từng trường hợp.

| Rank | ID | Câu hỏi | Distribution | Avg | Worst metric | Diagnosis | Suggested fix |
|---:|---:|---|---|---:|---|---|---|
| 1 | 39 | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | multi_hop | 0.1250 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 2 | 21 | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | multi_hop | 0.3750 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 3 | 33 | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | multi_hop | 0.3750 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 4 | 43 | Mật khẩu phải có tối thiểu bao nhiêu ký tự? | adversarial | 0.4167 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 5 | 48 | Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không? | adversarial | 0.4167 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 6 | 50 | Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không? | adversarial | 0.4167 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 7 | 9 | Nam nhân viên được nghỉ bao nhiêu ngày khi vợ sinh con? | factual | 0.5000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 8 | 44 | Bao lâu phải đổi mật khẩu một lần? | adversarial | 0.5000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 9 | 5 | Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt? | factual | 0.5000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 10 | 7 | Nghỉ phép không lương 20 ngày cần ai phê duyệt? | factual | 0.5811 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |

Tám câu trong top 10 có answer đúng nguyên văn là “Không tìm thấy.” dù contexts chứa thông tin để trả lời. Ví dụ ID 9 có context ghi nam nhân viên nghỉ 5 ngày làm việc khi vợ sinh con, nhưng answer bỏ qua dữ kiện; ID 5 có context về ngưỡng phê duyệt đơn trên 50 triệu đồng nhưng cũng không trả lời. Vì vậy, nhãn faithfulness mặc định “LLM hallucinating” không mô tả sát hành vi quan sát được ở các hàng này: đó chủ yếu là lỗi từ chối/abstain khi đã có bằng chứng. Cần chỉnh prompt để trả lời ngắn gọn theo context và chỉ từ chối khi context thực sự thiếu dữ kiện; sau đó đánh giá lại cùng bộ câu hỏi.

ID 39 là lỗi multi-hop rõ nhất: context có cả policy v1.0 (8 ký tự, 90 ngày) và v2.0 (12 ký tự, 120 ngày, MFA), nhưng answer vẫn từ chối thay vì tổng hợp và phân biệt phiên bản. ID 21 và 33 cũng có context về chính sách phép thâm niên/2024 cùng dữ kiện lương hoặc phụ cấp, nhưng answer không tổng hợp được các phần cần nối. ID 7 được trả lời một phần là CEO; context top có ngưỡng 16–30 ngày nhưng bị cắt trước phần điều kiện tự đóng bảo hiểm, phù hợp với worst metric `context_recall`.

Các trường hợp adversarial thể hiện hai loại bẫy. ID 43 và 44 truy xuất đồng thời policy mật khẩu cũ/mới; context chứa cả hai phiên bản, vì vậy câu trả lời cần ưu tiên v2.0 hiện hành (12 ký tự, đổi sau 120 ngày). ID 50 có context VPN ghi rõ không được dùng VPN cá nhân và phải dùng VPN WireGuard của công ty; answer lại từ chối. Với ID 48, context trả về bắt đầu bằng mảnh câu “được hưởng gói bảo hiểm sức khỏe PVI” nhưng thiếu phần phủ định đứng trước; đây là dấu hiệu chunking đã làm mất ngữ cảnh negation. Nên giữ câu phủ định cùng chunk và thêm kiểm tra version/current-policy trước khi trả lời.

## Matrix và nhóm yếu nhất

Matrix đếm mỗi câu một lần theo metric có điểm thấp nhất; tổng hàng là số câu, không phải chất lượng.

| Worst metric | factual | multi_hop | adversarial | Tổng |
|---|---:|---:|---:|---:|
| faithfulness | 3 | 13 | 4 | 20 |
| answer_relevancy | 15 | 7 | 5 | 27 |
| context_precision | 0 | 0 | 0 | 0 |
| context_recall | 2 | 0 | 1 | 3 |

Nhóm yếu theo mean thấp nhất: **adversarial**, mean **0.6581**. Worst metric xuất hiện nhiều nhất: **answer_relevancy**, 27/50 câu.

Adversarial thấp hơn multi_hop khoảng 0.0004 điểm, nên hai nhóm gần như ngang nhau; kết luận nhóm yếu nhất dựa đúng vào mean nhỏ nhất và không nên diễn giải chênh lệch này như một khác biệt lớn. So với factual (0.8271), adversarial thấp hơn khoảng 0.1690. `answer_relevancy` thấp ở cả ba nhóm, và nhiều câu answer abstain dù context có dữ kiện, nên ưu tiên sửa quy tắc trả lời/abstain, rồi kiểm thử lại trên cùng 50 câu. Với các lỗi multi-hop, bổ sung hướng dẫn tổng hợp nhiều nguồn và xác định phiên bản hiện hành. Với câu phủ định như ID 48, điều chỉnh ranh giới chunk để không tách từ phủ định khỏi mệnh đề quyền lợi.

## Bẫy adversarial và giới hạn

Hai câu mật khẩu (ID 43–44) chứa xung đột giữa v1.0 đã cũ và v2.0 hiện hành; câu VPN ID 50 yêu cầu phát hiện policy cấm dù cách diễn đạt gợi ý “tăng bảo mật”; câu PVI ID 48 phụ thuộc vào phủ định bị thiếu trong đoạn context được truy xuất. Các answer trong bottom 10 không chứng minh hệ thống đã nhận biết bẫy: “Không tìm thấy” không nêu được phiên bản đúng hay kết luận phủ định.

Kết quả chỉ đại diện cho 50 câu trong test set, corpus hiện tại, cấu hình generation đã lưu và hai model evaluator khai báo trong metadata. RAGAS là đánh giá tự động; cần spot-check thủ công trước khi xem các chênh lệch nhỏ là có ý nghĩa. Run này không đo tác động sau khi sửa prompt/chunking.
