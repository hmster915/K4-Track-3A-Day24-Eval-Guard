# Đánh giá LLM Judge Phase B

Nhóm: Chưa được cung cấp trong workspace.

Người phụ trách: Member 2.

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T16:19:49.416906+00:00.
Models generation/judge: `gpt-4o-mini-2024-07-18` / `gpt-4o-mini`.

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ `artifacts/answers_50q.json:answer`; B từ `fixtures/human_labels_10q.json:model_answer`; reference từ `fixtures/test_set_50q.json:ground_truth`. IDs: 1, 5, 12, 21, 41. Hai lượt dùng cùng question/reference; lượt đảo vị trí được quy về A/B gốc.

| ID | Candidate A | Candidate B | Pass 1 → Pass 2 (A/B gốc) | Final | Consistent | Scores pass 1 (A/B) | Scores pass 2 (A/B) | Reasoning hai lượt |
|---:|---|---|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc khi kết hôn. | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | B → B | B | Có | 0.8 / 1.0 | 0.8 / 1.0 | Lượt 1: Đáp án B cung cấp thông tin đầy đủ hơn về việc nghỉ có lương, trong khi đáp án A thiếu thông tin này. Lượt 2: Đáp án A chính xác và đầy đủ hơn vì có thông tin về việc nghỉ có lương, trong khi đáp án B thiếu thông tin này. |
| 5 | Cần Tổng Giám đốc (CEO) phê duyệt. | Cần Giám đốc phòng ban phê duyệt. | A → A | A | Có | 1.0 / 0.0 | 1.0 / 0.0 | Lượt 1: Đáp án A chính xác theo reference, trong khi đáp án B sai. Lượt 2: Đáp án B chính xác theo reference, trong khi đáp án A không đúng. |
| 12 | Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là 1 tháng lương. | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | A → tie | tie | Không | 1.0 / 0.7 | 1.0 / 1.0 | Lượt 1: Đáp án A cung cấp thông tin đầy đủ và chính xác về mức thưởng Tết tối thiểu cho nhân viên có từ 6 tháng trở lên, trong khi đáp án B chỉ nêu chung chung mà không chỉ rõ đối tượng và điều kiện. Lượt 2: Cả hai đáp án đều chính xác và đầy đủ thông tin như trong reference, không có sự khác biệt về nội dung. |
| 21 | Nhân viên Senior có 9 năm thâm niên sẽ được **18 ngày phép năm** (15 ngày cơ bản + 3 ngày cộng thêm cho thâm niên). Không tìm thấy thông tin về lương trong context. | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | B → B | B | Có | 0.8 / 1.0 | 0.7 / 1.0 | Lượt 1: Cả hai đáp án đều cung cấp thông tin về số ngày phép, nhưng đáp án B ngắn gọn và đầy đủ hơn về lương, trong khi đáp án A thiếu thông tin về lương. Lượt 2: Cả hai đáp án đều cung cấp thông tin về số ngày phép, nhưng đáp án A cung cấp thông tin về lương, trong khi đáp án B không có thông tin này, dẫn đến A chính xác và đầy đủ hơn. |
| 41 | Nhân viên chính thức được hưởng 12 ngày phép năm theo chính sách năm 2023 và 15 ngày phép năm theo chính sách năm 2024. Nhân viên có thâm niên từ 5 năm trở lên được cộng thêm 1 ngày phép cho mỗi 5 năm làm việc liên tục. | Nhân viên được nghỉ 12 ngày phép năm. | A → A | A | Có | 1.0 / 0.0 | 0.9 / 0.3 | Lượt 1: Đáp án A cung cấp thông tin chính xác về số ngày phép theo cả hai chính sách, ưu tiên chính sách mới nhất, trong khi đáp án B chỉ nêu thông tin theo chính sách cũ. Lượt 2: Đáp án B cung cấp thông tin chính xác về cả hai chính sách và nêu rõ số ngày phép theo chính sách hiện hành, trong khi đáp án A chỉ nêu số ngày phép theo chính sách cũ. |

Position inconsistency: **1/5 = 0.20**. Verbosity win rate: **3/4 = 0.75** trong các case quyết định. Chi tiết: candidate A dài hơn thắng 2 lần; candidate B dài hơn thắng 1 lần.

Position changed the mapped winner in 1/5 pairs. The longer answer won in 3/4 decisive cases. These five pairs are a small diagnostic sample; the rates indicate instability patterns, not proof that position or length caused a decision.

## Calibration đúng model_answer

Judge nhận đúng question, `model_answer` và ground truth từ fixtures. `human_label`/`human_note` không được đưa vào prompt; nhãn human chỉ được ghép sau khi judge trả kết quả.

| ID | model_answer gốc | Judge | Reasoning của judge | Human | Agree |
|---:|---|---:|---|---:|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | Câu trả lời chính xác theo reference, đầy đủ thông tin về số ngày nghỉ và điều kiện không trừ vào phép năm. | 1 | Có |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | Câu trả lời sai vì yêu cầu phê duyệt cho đơn hàng trên 50 triệu là từ Tổng Giám đốc, không phải Giám đốc phòng ban. | 0 | Có |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | Câu trả lời chính xác theo thông tin trong reference, nêu rõ điều kiện và mức thưởng cho nhân viên chính thức có từ 6 tháng trở lên. | 1 | Có |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | Câu trả lời chính xác theo reference, nêu rõ số ngày phép và khoảng lương cho nhân viên Senior với 9 năm thâm niên. | 1 | Có |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | Câu trả lời chính xác theo thông tin trong reference, nêu rõ rằng nhân viên phải hoàn trả 100% chi phí vì chưa đủ 1 năm cam kết. | 1 | Có |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | Câu trả lời sai vì không đề cập đến sự cần thiết có sự phê duyệt của Kế toán trưởng bên cạnh Trưởng phòng. Ngoài ra, phí phạt được tính cho quá hạn 15 ngày, không phải là 2% trên 8 triệu mà là 80.000 VNĐ. | 0 | Có |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | Câu trả lời cung cấp đúng số ngày phép và tổng phụ cấp hàng tháng theo thông tin trong tài liệu tham khảo. | 1 | Có |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | Câu trả lời sai vì nó dựa trên chính sách cũ (v2023) thay vì chính sách hiện hành (v2024) là 15 ngày phép năm. | 0 | Có |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | Câu trả lời chính xác theo reference, nêu rõ rằng nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần, đồng thời không bỏ qua phủ định quan trọng. | 1 | Có |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | Câu trả lời sai vì khẳng định rằng nhân viên Manager có thể dùng VPN cá nhân khi WFH, trong khi chính sách rõ ràng cấm việc này. | 0 | Có |

Cohen’s κ: **1.000**. Observed agreement `p_o = 1.00`; expected agreement `p_e = (6/10 × 6/10) + (4/10 × 4/10) = 0.52`. Vì vậy `κ = (p_o − p_e)/(1 − p_e) = 1.000`. Tập này đạt ngưỡng bonus κ > 0.6 trên đúng 10 câu đã gán nhãn.

## Giới hạn và cách dùng judge

Batch dùng `gpt-4o-mini`, temperature 0 và JSON response format; pairwise có 5 cặp × 2 thứ tự, calibration có 10 câu. Nhãn judge trùng 10/10 nhãn human. Đây là mẫu nhỏ, không chứng minh judge tổng quát hóa. Giữ swap-and-average vì kết quả có thể đổi theo vị trí; tie là lựa chọn thận trọng khi hai thứ tự không đồng thuận. Không dùng winner A/B thay nhãn tốt/xấu 0/1 vì hai tác vụ có đối tượng đánh giá khác nhau.
