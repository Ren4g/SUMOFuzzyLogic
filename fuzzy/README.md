# Bộ điều khiển đèn giao thông bằng logic mờ — Phần B

Module Python tính **thời gian đèn xanh dựa trên số xe đang chờ của hai hướng Bắc–Nam và Đông–Tây**. Bộ điều khiển sử dụng Mamdani với `scikit-fuzzy`: AND bằng `min`, cắt tập đầu ra bằng `min`, tổng hợp bằng `max`, giải mờ bằng trọng tâm (`centroid`).

Module chạy độc lập, **không cần SUMO để kiểm thử**. Phần kết nối SUMO, đọc hàng đợi, quản lý pha đèn và thu thập chỉ số do các module khác phụ trách.

## 1. Các file bàn giao

Đặt bốn file sau trong thư mục `fuzzy/` của repository nhóm:

| File | Chức năng |
| --- | --- |
| `membership_functions.py` | Tính mức thuộc Low/Medium/High và Short/Medium/Long bằng công thức, phục vụ minh họa và vẽ hình. |
| `fuzzy_controller.py` | Khai báo các biến mờ bằng thư viện, chứa bảng `RULES`, tạo bộ điều khiển, kiểm tra đầu vào và cung cấp `fuzzy_green_time()`. |
| `test_fuzzy.py` | Kiểm thử controller, minh họa một lần suy luận và vẽ Control Surface. |
| `README.md` | Hướng dẫn sử dụng và tích hợp. |

Thư mục `figures/` được tạo tự động khi chạy các hàm vẽ. Không cần các file cũ `fuzzy_rules.py`, `fuzzy_controller_skfuzzy.py` hoặc các script vẽ riêng. Nếu bản tải về có tên `test_fuzzy(1).py`, đổi tên thành `test_fuzzy.py` trước khi dùng các lệnh dưới đây.

> Lưu ý về bản hiện tại: hàm thuộc được định nghĩa ở cả `membership_functions.py` và `fuzzy_controller.py`. Hai nơi đang dùng cùng tham số. Khi thay đổi thiết kế, phải cập nhật đồng bộ để biểu đồ khớp với bộ điều khiển thực tế.

## 2. Cài đặt và chạy nhanh

Python 3.12 là phiên bản đã dùng để kiểm tra bộ code; lần kiểm tra dùng `scikit-fuzzy` 0.5.0. Mở terminal tại **thư mục gốc repository**, tức thư mục chứa `fuzzy/`.

```bash
python -m pip install numpy scipy networkx scikit-fuzzy matplotlib
```

Kiểm tra thư viện:

```bash
python -c "import skfuzzy; print(skfuzzy.__version__)"
```

Tên gói cài đặt là `scikit-fuzzy`, tên import là `skfuzzy`.

Chạy controller và bộ kiểm thử:

```bash
python fuzzy/fuzzy_controller.py
python fuzzy/test_fuzzy.py
```

Nếu đang đặt ba file Python ngay trong thư mục hiện tại, không có thư mục con `fuzzy/`, dùng `python fuzzy_controller.py` và `python test_fuzzy.py`.

**Chạy `test_fuzzy.py` trực tiếp bằng đường dẫn như trên.** Các import trong file này hiện được viết để tìm những file nằm cùng thư mục; chưa chuẩn hóa cho cách chạy `python -m fuzzy.test_fuzzy`.

## 3. Hàm để module điều khiển sử dụng

```python
def fuzzy_green_time(ns_queue: float, ew_queue: float) -> float:
    ...
```

| Thành phần | Ý nghĩa |
| --- | --- |
| `ns_queue` | Tổng số xe đang chờ trên các làn đầu vào thuộc Bắc và Nam. |
| `ew_queue` | Tổng số xe đang chờ trên các làn đầu vào thuộc Đông và Tây. |
| Giá trị trả về | Một số thực biểu diễn thời gian xanh Bắc–Nam, đơn vị giây. |

Đầu vào là **số xe đang chờ**, không phải tổng số xe đã đi qua, thời gian chờ hoặc số xe của toàn mạng đường. Khi đọc từ SUMO, cần tổng hợp đúng các làn đầu vào và tránh đếm trùng.

Quy ước xử lý đầu vào:

- Chấp nhận số không âm, hữu hạn; số nguyên và số thực đều dùng được.
- Từ 0 đến 40: sử dụng trực tiếp.
- Lớn hơn 40: chặn về 40 trước khi suy luận.
- Số âm, NaN hoặc vô cực: báo `ValueError`.
- Tham số được chuyển bằng `float()`; dữ liệu không chuyển được thành số sẽ gây lỗi chuyển kiểu.

Miền đầu ra thiết kế là **10–60 giây**. Không làm tròn trong hàm; chỉ dùng `:.2f` khi hiển thị. Trên lưới 441 điểm đã kiểm tra, đầu ra nằm khoảng **18,33–51,67 giây**; trọng tâm không nhất thiết chạm hai đầu miền 10 và 60.

## 4. Cách tính cho cả hai hướng

Đặt đoạn sau trong chương trình ở thư mục gốc repository, hoặc chạy chương trình tích hợp từ thư mục gốc theo hướng dẫn ở mục 5:

```python
from fuzzy.fuzzy_controller import fuzzy_green_time

ns_queue = 30
ew_queue = 5

ns_green = fuzzy_green_time(ns_queue, ew_queue)
ew_green = fuzzy_green_time(ew_queue, ns_queue)

print(f"Bắc–Nam: {ns_green:.2f} giây")
print(f"Đông–Tây: {ew_green:.2f} giây")
```

Kết quả với thiết kế hiện tại:

```text
Bắc–Nam: 40.42 giây
Đông–Tây: 29.58 giây
```

**Đảo thứ tự hai đầu vào để tính cho Đông–Tây.** Cách dùng này phù hợp vì hai hướng có cùng miền giá trị và thiết kế hàm thuộc. Có thể hiểu đối số thứ nhất là số xe của hướng cần tính, đối số thứ hai là số xe của hướng còn lại.

Nếu đoạn gọi nằm trong script chạy trực tiếp bên trong `fuzzy/`, dùng `from fuzzy_controller import fuzzy_green_time`.

## 5. Ghi chú tích hợp cho thành viên C

Trong `control/main.py`, có thể import:

```python
from fuzzy.fuzzy_controller import fuzzy_green_time
```

Từ thư mục gốc repository, chạy chương trình tích hợp bằng:

```bash
python -m control.main
```

Cách chạy này giúp Python tìm được thư mục `fuzzy/` cùng cấp với `control/`. Các thư mục phải có đúng tên và chứa code tương ứng; `control/main.py` là file của module C, không phải file do module B cung cấp.

Quy trình sử dụng:

1. Xác định các làn đầu vào thuộc nhóm Bắc–Nam và Đông–Tây; chỉ gộp những luồng tương thích với sơ đồ pha của ngã tư.
2. Tại thời điểm ra quyết định cho một pha, đọc và cộng số xe đang chờ của hai nhóm.
3. Gọi `fuzzy_green_time(ns_queue, ew_queue)` cho pha Bắc–Nam hoặc đảo đầu vào cho pha Đông–Tây.
4. Áp dụng thời gian đề xuất thông qua bộ quản lý pha của C; xử lý đèn vàng, khoảng đỏ an toàn và trình tự chuyển pha tại đó.

**Hàm chỉ trả về số giây, không bật đèn và không chọn ID pha.** Hai hướng xung đột không được cùng xanh. Thời gian vàng và đỏ chuyển tiếp không nằm trong giá trị trả về.

Nhóm cần thống nhất thời điểm đọc dữ liệu: tính cả hai pha từ cùng một lần quan sát, hoặc đọc lại trước từng pha. Nếu đọc lại khi bắt đầu pha Đông–Tây, thời gian tính được có thể khác ví dụ 29,58 giây vì hàng đợi đã thay đổi.

Không tự động gán lại toàn bộ thời gian xanh ở mọi bước mô phỏng: việc liên tục đặt lại thời gian còn lại có thể làm pha không kết thúc. Bộ quản lý pha phải quy định rõ thời điểm cập nhật.

Không giả định tổng hai thời gian xanh là 60 giây. Ví dụ trên có tổng 70 giây, chưa tính thời gian chuyển pha. Nếu muốn áp đặt chu kỳ cố định, nhóm phải thiết kế thêm cơ chế phân bổ thời gian.

## 6. Kiểm thử và thử một cặp đầu vào

`test_fuzzy.py` có ba chức năng chính:

| Hàm | Chức năng |
| --- | --- |
| `test_controller()` | So sánh 6 ca tham chiếu, kiểm tra đầu ra, chặn trên 40 xe và từ chối dữ liệu sai. |
| `plot_fuzzy_process(ns_queue, ew_queue)` | Vẽ hàm thuộc hai đầu vào, các tập đầu ra sau cắt, vùng tổng hợp và trọng tâm cho một cặp đầu vào. |
| `plot_control_surface()` | Tính 21 × 21 = 441 cặp trên miền 0–40 xe, rồi vẽ bề mặt 3D và bản đồ màu. |

Để chỉ kiểm thử, sửa khối cuối `test_fuzzy.py` thành:

```python
if __name__ == "__main__":
    test_controller()
```

Để chạy đủ các phần:

```python
if __name__ == "__main__":
    test_controller()
    plot_fuzzy_process(30, 5)
    plot_control_surface()
```

Đóng cửa sổ hình thứ nhất để chương trình tiếp tục sang Control Surface, vì mỗi hàm vẽ gọi `plt.show()`.

Muốn thử số xe khác, đổi hai đối số của `plot_fuzzy_process()`, lưu file rồi chạy lại. Việc này **không thay đổi** danh sách ca kiểm thử và lưới khảo sát của Control Surface. Điểm đỏ `(30, 5)` trong Control Surface cũng đang được ghi cố định trong hàm vẽ.

Giá trị tham chiếu của thiết kế hiện tại:

| Bắc–Nam | Đông–Tây | Xanh Bắc–Nam (giây, làm tròn) |
| ---: | ---: | ---: |
| 30 | 5 | 40,4167 |
| 5 | 30 | 29,5833 |
| 20 | 20 | 35,0000 |
| 40 | 0 | 51,6667 |
| 0 | 40 | 18,3333 |
| 0 | 0 | 35,0000 |

Kiểm thử cho phép sai lệch dưới 0,02 giây so với giá trị tham chiếu. Khi đổi hàm thuộc hoặc bảng luật, phải xem lại các giá trị này theo thiết kế mới.

## 7. Các file kết quả

Được lưu trong `figures/` bên cạnh `test_fuzzy.py`:

| File | Nội dung |
| --- | --- |
| `fuzzy_process_ns_30_ew_5.png` | Ví dụ ảnh suy luận cho NS=30, EW=5; tên ảnh thay đổi theo hai đầu vào. |
| `control_surface.png` | Bề mặt 3D và bản đồ màu của bộ điều khiển. |
| `control_surface.csv` | 441 dòng số liệu, các cột `ns_queue,ew_queue,green_time`. |

Chạy lại cùng trường hợp sẽ ghi đè ảnh cùng tên; chạy lại Control Surface sẽ ghi đè PNG và CSV của nó.

**Đây là kết quả khảo sát thuật toán**, không phải số liệu Average Waiting Time, Average Queue Length hoặc Throughput từ SUMO. Thành viên D cần thu thập các chỉ số đó khi chạy mô phỏng để so sánh Fuzzy với Fixed-Time.

## 8. Tham số và bảng luật hiện tại

Các mốc là cấu hình ban đầu để thử nghiệm, chưa được tối ưu theo mạng đường cụ thể.

| Biến | Miền | Các tập mờ tam giác `[a, b, c]` |
| --- | --- | --- |
| `ns_queue`, `ew_queue` | 0–40 xe | Low `[0, 0, 20]`; Medium `[0, 20, 40]`; High `[20, 40, 40]` |
| `green_time` | 10–60 giây | Short `[10, 10, 35]`; Medium `[10, 35, 60]`; Long `[35, 60, 60]` |

Mọi ô dưới đây là kết luận cho hướng ở đối số thứ nhất, mặc định Bắc–Nam:

| Bắc–Nam / Đông–Tây | Low | Medium | High |
| --- | --- | --- | --- |
| Low | Medium | Short | Short |
| Medium | Long | Medium | Short |
| High | Long | Long | Medium |

Giới hạn cần biết:

- Trên 40 xe bị bão hòa: `(50, 20)` và `(80, 20)` đều được tính như `(40, 20)`.
- Với hai hàng đợi bằng nhau, thiết kế đối xứng hiện tại cho khoảng 35 giây; chưa phân biệt tốt tổng tải thấp và cao khi hai hướng cân bằng.
- `(0, 0)` vẫn trả về 35 giây theo luật Low–Low → Medium. Xử lý giữ pha hoặc bỏ qua pha không có xe cần được nhóm thống nhất riêng.
- Chưa dùng thời gian chờ, xe ưu tiên, hàng đợi từng làn hoặc bốn đầu vào riêng biệt.
- Bộ điều khiển không tự bảo đảm thời gian chờ tối đa hay xử lý mọi xung đột rẽ; cần bộ quản lý pha và đánh giá trong mô phỏng.
- Các hàm minh họa `evaluate_rules()` và `aggregated_membership()` trong file test tái hiện phép tính để vẽ; giá trị xanh chính thức lấy từ `fuzzy_green_time()` dùng `scikit-fuzzy`.

## 9. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| `No module named 'skfuzzy'` | Cài bằng `python -m pip install scikit-fuzzy`; bảo đảm VS Code chọn đúng Python đã cài thư viện. |
| Thiếu `networkx`, `scipy` hoặc `matplotlib` | Chạy lại lệnh cài đầy đủ ở mục 2. |
| Không tìm thấy `fuzzy_controller` khi chạy test | Giữ ba file Python cùng thư mục và chạy trực tiếp `python fuzzy/test_fuzzy.py` từ thư mục gốc. |
| Không tìm thấy `fuzzy` khi chạy module C | Chạy từ thư mục gốc repository bằng `python -m control.main`; kiểm tra tên thư mục. |
| Đổi số xe nhưng bảng test và Control Surface không đổi | Đây là các phần độc lập; chỉ hình `plot_fuzzy_process(...)` dùng cặp đầu vào vừa đổi. |
| Chương trình dừng sau hình đầu tiên | Đóng cửa sổ biểu đồ để chạy tiếp; Control Surface có thông báo tiến độ từng hàng. |
| Lỗi hiển thị tiếng Việt ở terminal | Thử chạy `python -X utf8 fuzzy/test_fuzzy.py`. |

Khi cài thư viện xong nhưng VS Code vẫn báo thiếu, kiểm tra đường dẫn bằng `python -c "import sys; print(sys.executable)"`, rồi chọn đúng đường dẫn trong **Python: Select Interpreter**.
