# Đánh giá LLM Judge Phase B

Nhóm: Chưa ghi tên nhóm trong workspace.

Người phụ trách: Chưa được cung cấp.

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T14:45:39.883958+00:00.
Models generation/judge: `gpt-4o-mini-2024-07-18` / `gpt-4o-mini`.

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ `artifacts/answers_50q.json:answer`; B từ `fixtures/human_labels_10q.json:model_answer`; reference từ `fixtures/test_set_50q.json:ground_truth`. IDs: 1, 5, 12, 21, 41. Cả hai lượt dùng cùng question và reference; lượt hai đảo vị trí rồi quy winner/scores về A/B ban đầu.

| ID | Candidate A | Candidate B | Pass 1 → Pass 2 (quy về A/B gốc) | Final | Consistent | Scores pass 1 (A/B) | Scores pass 2 (A/B) | Reasoning hai lượt |
|---:|---|---|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc khi kết hôn. | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | B → B | B | Có | 0.8 / 1.0 | 0.8 / 1.0 | Lượt 1: B nêu rõ ngày nghỉ có lương; A thiếu điều kiện này. Lượt 2: A (candidate gốc B) đầy đủ, B (candidate gốc A) thiếu điều kiện nghỉ có lương. |
| 5 | Không tìm thấy. | Cần Giám đốc phòng ban phê duyệt. | B → A | tie | Không | 0.0 / 0.5 | 0.5 / 0.0 | Lượt 1: B có thông tin liên quan nhưng chưa chính xác hoàn toàn; A không cung cấp thông tin. Lượt 2: candidate gốc A bị xem là sai lệch, candidate gốc B bị xem là không có thông tin. |
| 12 | Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là 1 tháng lương. | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | A → tie | tie | Không | 1.0 / 0.8 | 1.0 / 1.0 | Lượt 1: A nêu rõ đối tượng và điều kiện; B chung chung. Lượt 2: judge xem cả hai đúng và đủ theo reference. |
| 21 | Không tìm thấy. | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | B → B | B | Có | 0.0 / 1.0 | 0.0 / 1.0 | Cả hai lượt chọn candidate gốc B vì trả lời đúng, đủ số ngày phép và khoảng lương; candidate gốc A không có nội dung trả lời. |
| 41 | Nhân viên chính thức được hưởng 15 ngày phép năm có lương. | Nhân viên được nghỉ 12 ngày phép năm. | A → A | A | Có | 1.0 / 0.0 | 1.0 / 0.0 | Cả hai lượt chọn candidate gốc A theo policy v2024 hiện hành; B dùng policy cũ. |

Position inconsistency: **2/5 = 0.40** (IDs 5 và 12 đổi kết quả sau khi quy lượt đảo về A/B gốc). Verbosity win rate: **3/3 = 1.00** trong các case quyết định; ID 1 và 21 chọn B dài hơn, ID 41 chọn A dài hơn. Hai case còn lại là tie nên không đưa vào mẫu số.

Đây là dấu hiệu cần theo dõi, chưa chứng minh judge ưu tiên vị trí hay độ dài. Có 5 cặp, hai case bất đồng và ba case quyết định; ở ID 1/41 phần dài hơn cũng chứa thông tin quan trọng về nghỉ có lương hoặc phiên bản chính sách, nên độ chính xác và độ dài đang đồng biến. Nên kiểm tra thêm nhiều cặp với nội dung đúng/sai được cân bằng độ dài trước khi kết luận verbosity bias.

## Calibration đúng model_answer

Judge nhận đúng question, `model_answer` và ground truth từ fixtures. `human_label`/`human_note` không được đưa vào prompt; nhãn human chỉ được ghép sau khi judge trả kết quả.

| ID | model_answer gốc | Judge | Reasoning của judge | Human | Agree |
|---:|---|---:|---|---:|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | Đúng reference; nêu số ngày nghỉ và điều kiện không trừ vào phép năm. | 1 | Có |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | Sai người phê duyệt; cần Tổng Giám đốc thay vì Giám đốc phòng ban. | 0 | Có |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | Đúng reference; đáp ứng điều kiện và mức thưởng. | 1 | Có |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | Đúng reference; đủ số ngày phép và khoảng lương. | 1 | Có |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | Đúng chính sách hoàn trả trước khi đủ 1 năm cam kết. | 1 | Có |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | Thiếu phê duyệt Kế toán trưởng và mô tả sai phí phạt/quá hạn. | 0 | Có |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | Đúng số ngày phép và tổng phụ cấp theo reference. | 1 | Có |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | Dùng policy cũ v2023; policy hiện hành v2024 quy định 15 ngày. | 0 | Có |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | Đúng reference; nêu không có phép năm và phải xin nghỉ không lương nếu cần. | 1 | Có |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | Sai vì policy cấm VPN cá nhân. | 0 | Có |

Cohen’s κ: **1.000**. Observed agreement `p_o = 10/10 = 1.00`. Tỷ lệ nhãn human là 6/10 positive và 4/10 negative; expected agreement `p_e = (0.6×0.6) + (0.4×0.4) = 0.52`. Do đó `κ = (p_o − p_e)/(1 − p_e) = 1.00`. Tập này đạt ngưỡng bonus κ > 0.6, nhưng chỉ có 10 nhãn và không chứng minh judge tổng quát hóa trên dữ liệu khác.

## Giới hạn và cách dùng judge

Batch sử dụng `gpt-4o-mini`, temperature 0 và JSON response format; pairwise có 5 cặp × 2 thứ tự, calibration có 10 câu. Nhãn judge trùng toàn bộ nhãn human trong mẫu này. Cần xem κ như agreement trên đúng 10 câu, không phải độ chính xác phổ quát. Các lượt pairwise không nhất quán ở ID 5 và 12 cho thấy nên giữ swap-and-average; tie là kết quả thận trọng khi hai thứ tự không đồng thuận. Không dùng winner A/B thay cho nhãn tốt/xấu 0/1 vì hai tác vụ có đối tượng đánh giá khác nhau.
