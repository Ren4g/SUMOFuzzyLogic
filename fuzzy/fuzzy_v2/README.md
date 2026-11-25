# Fuzzy V2 — đổi folder, giữ cách gọi hàm

Đặt thư mục `fuzzy_v2` cạnh thư mục `fuzzy` cũ trong dự án. Không ghi đè bản cũ.
Bản này tự chứa lõi fuzzy, không import code từ thư mục `fuzzy`.

## Dùng ngay

Trong code đang gọi bộ điều khiển, thay:

```python
from fuzzy.fuzzy_controller import fuzzy_green_time
```

bằng:

```python
from fuzzy.fuzzy_v2.fuzzy_controller import fuzzy_green_time
```

Giữ nguyên lệnh gọi:

```python
green_seconds = fuzzy_green_time(ns_queue, ew_queue)
```

Hàm trả về `float` trong [10, 60] giây cho nhóm ở tham số THỨ NHẤT.
Muốn tính cho Đông–Tây: `fuzzy_green_time(ew_queue, ns_queue)`.
Đầu vào là tổng xe ĐANG CHỜ trên các làn phục vụ của mỗi nhóm, không phải mọi xe trên đường.
Nên gọi tại đầu pha xanh chính. Hàm không tự gọi TraCI hoặc thay đổi thứ tự pha/vàng/đỏ.
Không gọi lặp rồi đặt lại toàn bộ thời gian mỗi bước SUMO, vì việc đó có thể kéo dài pha ngoài ý muốn.

Thư mục này KHÔNG thêm chế độ `--mode fuzzy_v2` vào runner. Trưởng nhóm tự chọn import/nhãn
kết quả trong chương trình chung; cần ghi rõ tên controller khi so sánh CSV để tránh nhầm baseline.

## File trong folder

- `fuzzy_controller.py`: tất cả lõi Mamdani và hiệu chỉnh V2 nằm trong file này.
- `membership_functions.py`: giữ nguyên các hàm thuộc của baseline để minh họa.
- `test_fuzzy.py`: kiểm tra V2; có thể tạo hình và CSV bề mặt điều khiển.
- `README.md`: tích hợp, phương pháp và kết quả chạy thử.

Không cần file adapter mới trong `control/`. Không phụ thuộc vào `fuzzy_controller_v2.py` cũ.
Các hàm thuộc vẫn dùng miền 0–40; khi minh họa đầu vào lớn, chuẩn hóa cả cặp bằng
`normalize_queues()` trước. `membership_functions.py` riêng lẻ vẫn chặn đầu vào như baseline.

## Cải tiến

1. Giữ 9 luật Mamdani min–max và giải mờ centroid của baseline.
2. Chuẩn hóa chung cặp đầu vào: `scale = 40 / max(40, own, other)`.
   Ví dụ (80, 40) thành (40, 20), thay vì (40, 40).
3. Giảm xanh theo mức nhu cầu:
   `green = 10 + min(own / 20, 1) * (mamdani_green - 10)`.
   Đây là hiệu chỉnh heuristic sau fuzzy, không phải bộ Mamdani mới có nhiều đầu vào.
   Ngưỡng 20 được chọn bằng tìm kiếm ứng viên trên mô phỏng, thay ngưỡng 5 của bản V2 thủ công.
4. Hướng không có xe chờ trả về 10 giây. Chưa dự báo xe đang tiến tới.
5. Cache tối đa 4096 kết quả lõi Mamdani; không làm tròn số xe, không lưu trạng thái giao thông.
6. Kiểm tra NaN, vô cực, số âm và giới hạn đầu ra 10–60 giây.

Ví dụ khi không truyền thời gian chờ: (0,0) → 10; (1,1) → 11.25;
(5,5) → 16.25; (20,20) → 35 giây. Hai hướng cân bằng nhưng ít xe không còn nhận 35 giây.

## Thời gian chờ tùy chọn

```python
green_seconds = fuzzy_green_time(
    own_queue, other_queue,
    own_wait=longest_own_wait,
    other_wait=longest_other_wait,
)
```

`own_wait` và `other_wait` là thời gian chờ liên tục lớn nhất của xe trong mỗi nhóm, đơn vị giây.
Nếu chỉ gọi hai đối số thì cả hai bằng 0, phần này không tác động.
Cộng thêm `10 * (min(own_wait/60, 1) - min(other_wait/60, 1))` giây, sau đó chặn 10–60.
Bỏ qua other_wait nếu nhóm kia không có xe; nhóm own trống luôn trả về 10.
Các ngưỡng 60 và 10 của phần tùy chọn này CHƯA được tối ưu bằng mô phỏng.
Chỉ có kiểm tra chức năng cho nhánh này. Toàn bộ số liệu bên dưới dùng đúng HAI đầu vào.
Không đảm bảo mọi xe chờ dưới 60 giây; không có cơ chế chống bỏ đói tuyệt đối hoặc cập nhật mỗi 5 giây.

## Kiểm tra nhanh

Tại thư mục gốc dự án, dùng cùng Python đã cài dependency của bản cũ:

```powershell
python fuzzy_v2/fuzzy_controller.py
python fuzzy_v2/test_fuzzy.py
python fuzzy_v2/test_fuzzy.py --plot
```

Lệnh cuối sinh `fuzzy_v2/figures/control_surface.png` và `.csv` của V2.
Nếu thiếu thư viện: `python -m pip install numpy scipy networkx scikit-fuzzy==0.5.0 matplotlib`.
Đã qua 7 nhóm kiểm tra: lõi cũ, ít xe, cặp lớn, dữ liệu sai, thời gian chờ tùy chọn,
giới hạn/lặp lại và tương thích lời gọi keyword cũ. Đã chạy cả dạng script và module.

## Chọn tham số và kiểm chứng

SUMO/traci/sumolib 1.28.0, scikit-fuzzy 0.5.0; bước mô phỏng 0.1 giây.
Hai mạng và luồng xe gốc lấy tại commit trên; kịch bản dense dùng mạng 3 làn và `--scale 2`.
Các trường hợp lần lượt có 600, 1940, 3880 xe. Giữ adapter baseline để chỉ thay hàm tính thời gian.
Không đổi thứ tự pha, pha vàng hoặc pha rẽ riêng. Tính một lần tại đầu mỗi pha xanh chính.
Chạy đến khi hết xe (ghi đè thời điểm kết thúc thành 100000; có chặn vòng lặp tại 15000 giây).
Đo `waitingTime` và `timeLoss` của xe hoàn thành từ tripinfo.xml; mọi lượt đều hết xe.

Tìm kiếm: seed 1, 3 kịch bản, 8 phương án = 24 lượt:

- baseline;
- manual_v2: hệ số activity với ngưỡng 5;
- activity10, activity20: ngưỡng 10 hoặc 20;
- cap1, cap2, cap3: `min(mamdani_green, 10 + k * own)`;
- fixed10: đối chứng đơn giản, đặt hai pha xanh chính luôn 10 giây.

Các phương án cải tiến cùng chuẩn hóa tỷ lệ đầu vào; own=0 trả về 10.
Mục tiêu chọn ứng viên thích nghi: trung bình trên 3 kịch bản của tỷ lệ thời gian chờ so với baseline,
với điều kiện hết xe, không collision/teleport. `activity20` có điểm 0.525208,
so với cap1 0.536536, cap2 0.570748, activity10 0.594256, cap3 0.623871.
Giữ nguyên ngưỡng 20, kiểm chứng trên seed 11 và 23, không dùng các seed này để chọn tham số.
Kiểm chứng gọi trực tiếp file `fuzzy_v2/fuzzy_controller.py` được bàn giao.

### Kết quả kiểm chứng — trung bình hai seed 11 và 23

Đơn vị: giây chờ trung bình mỗi xe; cột giảm so với baseline.

| Kịch bản                | Baseline | V2 thủ công trước | V2 gộp này |  Giảm |
| ----------------------- | -------: | ----------------: | ---------: | ----: |
| 4 hướng 2 làn           |    10.38 |              6.31 |       3.28 | 68.4% |
| 4 hướng 3 làn           |    16.07 |             13.01 |      10.80 | 32.8% |
| 3 làn, lượng xe gấp đôi |    20.47 |             20.45 |      12.03 | 41.2% |

Tất cả 42 lượt tìm kiếm + kiểm chứng: pending=0, collision=0, teleport=0.
Đây là quan sát trên mô phỏng, không phải chứng nhận an toàn hay bảo đảm hiệu quả trên mọi mạng.

Nguồn API: [scikit-fuzzy control](https://scikit-fuzzy.readthedocs.io/en/latest/api/skfuzzy.control.html),
[SUMO setPhaseDuration](https://sumo.dlr.de/docs/TraCI/Change_Traffic_Lights_State.html).

## Dữ liệu từng lượt chạy để đối chiếu

`dropin` là file bàn giao; `activity20` là ứng viên tương đương trong bước chọn tham số.
P95 và max là thời gian chờ mỗi xe. Mỗi hàng đều hoàn thành đủ số xe của kịch bản,
không pending/collision/teleport.

| Tập        | Kịch bản | Seed | Phương án  |  Chờ TB |   P95 |    Max | Time loss TB |
| ---------- | -------- | ---: | ---------- | ------: | ----: | -----: | -----------: |
| Chọn       | dense    |    1 | activity10 | 15.0349 | 44.20 |  62.80 |      22.4699 |
| Chọn       | dense    |    1 | activity20 | 12.0281 | 35.70 |  47.00 |      18.9103 |
| Chọn       | dense    |    1 | baseline   | 19.8815 | 56.40 | 112.00 |      28.5891 |
| Chọn       | dense    |    1 | cap1       | 11.8419 | 34.70 |  42.70 |      18.8040 |
| Chọn       | dense    |    1 | cap2       | 13.8240 | 40.60 |  55.90 |      21.0436 |
| Chọn       | dense    |    1 | cap3       | 16.1287 | 47.10 |  78.20 |      23.7406 |
| Chọn       | dense    |    1 | fixed10    | 10.1058 | 29.30 |  32.10 |      16.8330 |
| Chọn       | dense    |    1 | manual_v2  | 20.9161 | 64.40 | 140.30 |      29.8510 |
| Chọn       | three    |    1 | activity10 | 11.5925 | 33.20 |  42.00 |      16.5456 |
| Chọn       | three    |    1 | activity20 | 10.7902 | 30.70 |  36.00 |      15.7337 |
| Chọn       | three    |    1 | baseline   | 16.0736 | 51.80 |  60.20 |      21.3360 |
| Chọn       | three    |    1 | cap1       | 10.8549 | 30.60 |  35.20 |      15.8463 |
| Chọn       | three    |    1 | cap2       | 11.2761 | 32.40 |  41.20 |      16.2277 |
| Chọn       | three    |    1 | cap3       | 12.1097 | 35.30 |  45.70 |      17.1278 |
| Chọn       | three    |    1 | fixed10    | 10.1691 | 28.70 |  31.50 |      15.0696 |
| Chọn       | three    |    1 | manual_v2  | 13.7796 | 43.80 |  57.60 |      18.7795 |
| Chọn       | two      |    1 | activity10 |  3.3208 | 10.50 |  20.90 |       7.6671 |
| Chọn       | two      |    1 | activity20 |  3.2557 | 12.40 |  19.00 |       7.5289 |
| Chọn       | two      |    1 | baseline   | 10.8763 | 34.80 |  49.30 |      17.9058 |
| Chọn       | two      |    1 | cap1       |  3.6833 | 13.40 |  20.80 |       8.1406 |
| Chọn       | two      |    1 | cap2       |  3.4303 | 10.90 |  17.10 |       7.7562 |
| Chọn       | two      |    1 | cap3       |  3.3388 | 10.40 |  21.60 |       7.6546 |
| Chọn       | two      |    1 | fixed10    |  3.9175 | 13.10 |  21.70 |       8.5464 |
| Chọn       | two      |    1 | manual_v2  |  6.0923 | 22.30 |  29.30 |      11.4720 |
| Kiểm chứng | dense    |   11 | baseline   | 20.1253 | 56.10 | 143.30 |      28.8086 |
| Kiểm chứng | dense    |   11 | dropin     | 12.1435 | 35.50 |  44.60 |      19.0844 |
| Kiểm chứng | dense    |   11 | manual_v2  | 20.4746 | 58.50 | 147.60 |      29.2878 |
| Kiểm chứng | dense    |   23 | baseline   | 20.8152 | 61.00 | 151.50 |      29.7306 |
| Kiểm chứng | dense    |   23 | dropin     | 11.9187 | 35.50 |  46.80 |      18.7355 |
| Kiểm chứng | dense    |   23 | manual_v2  | 20.4344 | 58.50 | 139.50 |      29.2170 |
| Kiểm chứng | three    |   11 | baseline   | 16.1188 | 51.60 |  60.30 |      21.3618 |
| Kiểm chứng | three    |   11 | dropin     | 10.8363 | 30.90 |  35.90 |      15.8108 |
| Kiểm chứng | three    |   11 | manual_v2  | 13.2947 | 42.10 |  55.20 |      18.1705 |
| Kiểm chứng | three    |   23 | baseline   | 16.0154 | 51.40 |  72.40 |      21.2524 |
| Kiểm chứng | three    |   23 | dropin     | 10.7553 | 30.70 |  36.10 |      15.6751 |
| Kiểm chứng | three    |   23 | manual_v2  | 12.7280 | 40.60 |  52.10 |      17.5730 |
| Kiểm chứng | two      |   11 | baseline   | 10.3105 | 34.70 |  45.70 |      17.1665 |
| Kiểm chứng | two      |   11 | dropin     |  3.2615 | 11.60 |  20.50 |       7.4968 |
| Kiểm chứng | two      |   11 | manual_v2  |  6.5513 | 23.20 |  34.00 |      12.0623 |
| Kiểm chứng | two      |   23 | baseline   | 10.4440 | 34.70 |  46.20 |      17.2091 |
| Kiểm chứng | two      |   23 | dropin     |  3.2922 | 12.10 |  19.80 |       7.5334 |
| Kiểm chứng | two      |   23 | manual_v2  |  6.0700 | 22.50 |  30.00 |      11.4286 |
