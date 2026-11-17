## NOTE
tripinfo (viết đầy đủ là Trip Information, file tripinfo.xml) là file nhật ký kết quả mô phỏng của SUMO, nếu tên của người đọc là Võ Hoàng Thông, người đó sẽ ăn ngủ với file này.

## Mục tiêu và trạng thái

Ban đầu `control/` chạy được với `sumo/`, `fuzzy/` có luật fuzzy nhưng chưa được gọi trong vòng lặp SUMO, còn `evaluation/` là các script hậu xử lý độc lập. Đợt tích hợp này nối thành luồng:

```text
sumo scenario → control/TraCI → đo hàng chờ theo pha → fuzzy policy → SUMO tripinfo
                                              ↓
                           evaluation CSV → summary → comparison/chart
```

Luật fuzzy gốc được giữ nguyên. Cả hai kịch bản có sẵn và kịch bản demo mới đã chạy được với controller fuzzy; report tạo được kết quả theo kịch bản và seed. Hệ thống hiện vẫn giả định có đúng hai pha xanh chính đối xứng. Đây là bản tích hợp và đánh giá ban đầu, chưa phải xác nhận hiệu quả tổng quát.

## 1. `control/` — tích hợp và điều phối

### Phần đã làm tốt

- Đã có vòng lặp TraCI ổn định để khởi chạy SUMO, đọc trạng thái đèn/hàng chờ và thu `tripinfo`.
- Phần điều khiển đèn và phần đọc dữ liệu đã tách thành module nhỏ, thuận tiện để thêm controller mới.

### Đã bổ sung trong đợt tích hợp

- Thêm mode `fuzzy` vào CLI và GUI; thêm seed SUMO có thể đặt từ GUI hoặc CLI.
- Tạo `control/fuzzy_phase_controller.py`: lấy pha và controlled-link từ SUMO, xác định hai pha xanh chính, gom các làn đầu vào phục vụ bởi từng pha, rồi gọi API fuzzy khi pha chính bắt đầu.
- Fuzzy chỉ đổi thời lượng của hai pha xanh chính. Pha vàng và pha rẽ riêng, ví dụ hai pha rẽ trái 6 giây ở mạng 3 làn, giữ thời lượng trong chương trình SUMO.
- Chỉnh mode `fixed` để chỉ đặt thời lượng hai pha chính; không kéo dài nhầm pha xanh rẽ trái riêng thành 30 giây.
- Mỗi run ghi metadata kịch bản, controller, seed và các chỉ số vào summary đánh giá.

### Việc cần làm tiếp

- Thêm policy xử lý pha chính không có xe: hiện controller vẫn luân phiên pha và fuzzy vẫn cấp xanh khác 0 cho hướng trống.
- Đặt rõ giới hạn xanh tối thiểu/tối đa và chính sách chống bỏ đói; hiện fuzzy dùng miền 10–60 giây của model.
- Chuyển cách nhận diện pha thành cấu hình kiểm tra được nếu bổ sung mạng không có đúng hai pha chính đồng hạng. Adapter hiện báo lỗi nếu không nhận diện chính xác hai pha đó.

## 2. `sumo/` — mạng và kịch bản giao thông

### Phần đã làm tốt

- Hai kịch bản cũ cung cấp các mạng có cấu trúc khác nhau: giao lộ hai làn với hai pha chính, và giao lộ ba làn có thêm pha rẽ trái riêng.
- Tệp mạng khai báo trạng thái tín hiệu và controlled-link đủ để control ánh xạ pha sang các làn SUMO mà không phải gán cứng ID làn trong code.

### Đã bổ sung trong đợt tích hợp

- Thêm `sumo/fuzzy_adaptive_demo/`: dùng lại mạng hai làn, nhưng nhu cầu lệch mạnh Bắc–Nam trong 1.800 giây đầu rồi chuyển sang Đông–Tây trong 1.800 giây sau.
- Fixed và fuzzy dùng cùng route, lượng xe và seed. Đây là tình huống minh họa để quan sát fuzzy phân bổ xanh theo sự thay đổi hàng chờ.
- Có README và lệnh chạy riêng cho kịch bản demo.

### Việc cần làm tiếp

- Bổ sung bộ benchmark có các mức tải nhẹ, bão hòa, lệch hướng cố định và đổi hướng; tránh chỉ đánh giá trên một kịch bản được thiết kế để làm nổi bật tính thích nghi.
- Kiểm tra nhu cầu và năng lực từng hướng để đảm bảo mọi kịch bản đại diện cho mục tiêu so sánh đã định.
- Nếu thêm sơ đồ nhiều hơn hai nhóm pha chính, mô tả rõ movement conflict và pha phục vụ trong dữ liệu/configuration của kịch bản.

## 3. `fuzzy/` — luật và giao diện suy luận

### Phần đã làm tốt

- API của model gọn, nhận hai giá trị hàng chờ và trả thời lượng xanh; các luật Mamdani, kiểm tra đầu vào và miền giá trị được tách khỏi TraCI.
- Có ca tham chiếu và mô tả cách dùng độc lập với SUMO. Điều này cho phép thay đổi model mà không buộc fuzzy tự điều khiển trình tự tín hiệu.

### Đã bổ sung trong đợt tích hợp

- Giữ nguyên toàn bộ rule base. Adapter control gọi cùng một hàm cho cả hai hướng bằng cách đảo thứ tự hai queue.
- Khóa rõ hợp đồng hiện tại: đầu vào là tổng xe dừng trên làn thuộc pha chính đang xét và pha đối diện; đầu ra là thời lượng xanh của pha đang xét.
- Cập nhật README để trỏ tới adapter đang dùng thật, không còn dựa vào ví dụ `control/main.py` không có trong repo.

### Việc cần làm tiếp

- Nghiên cứu xử lý hàng chờ bằng 0 và chọn pha: model hiện không thể trả “bỏ qua pha”; với hai đầu vào 0, đầu ra khoảng 35 giây, còn hướng trống vẫn có thể nhận khoảng 18 giây khi hướng kia đông.
- Chỉ sửa luật sau khi chỉ rõ mục tiêu và so sánh qua nhiều seed. Lưu baseline hiện tại để mọi thay đổi đều có thể đối chiếu.
- Nếu cần điều khiển riêng pha rẽ, thiết kế phiên bản interface mới có chủ đích; không đổi ngầm nghĩa của hai đầu vào hiện tại.

## 4. `evaluation/` — thu thập và so sánh

### Phần đã làm tốt

- Pipeline được tách thành chuyển `tripinfo` sang CSV từng xe, tính metrics, so sánh summary và vẽ chart.
- Có alias để đọc tên thuộc tính phổ biến trong SUMO như `waitingTime`, `timeLoss`, `routeLength`.

### Đã bổ sung trong đợt tích hợp

- Mỗi run control tự gọi evaluation và ghi CSV xe cùng summary vào `results/evaluation/`.
- Summary lưu controller, scenario, run ID và seed. `evaluation.report_results` tạo comparison CSV/PNG, tách theo scenario và có thể lọc seed.
- Biểu đồ hỗ trợ số controller tùy ý và báo lỗi rõ khi thiếu cột metrics.

### Việc cần làm tiếp

- Report hiện hiển thị từng run; chưa gộp nhiều seed, tính độ lệch chuẩn/khoảng tin cậy, hay ghép cặp thống kê theo seed.
- Thống nhất chính thức cách diễn giải throughput và cách báo cáo xe chưa hoàn tất. Các trung bình hiện dựa trên các chuyến có trong `tripinfo`.
- Bổ sung bảng/biểu đồ tổng hợp nhiều seed để dùng ra quyết định thay đổi fuzzy.

## Kết quả chạy kiểm chứng

Đã chạy fixed và fuzzy cho `fuzzy_adaptive_demo` với cùng seed `1`; cả hai hoàn tất 4.644 chuyến. Kết quả một lần chạy:

| Chỉ số | Fixed | Fuzzy | Thay đổi quan sát được |
| --- | ---: | ---: | ---: |
| Thời gian mô phỏng đến khi xe hoàn tất | 3.790 s | 3.621 s | fuzzy sớm hơn 169 s |
| Thời gian chờ trung bình | 6,26 s | 5,41 s | giảm khoảng 13,7% |
| Time loss trung bình | 8,77 s | 7,42 s | giảm khoảng 15,4% |
| Số chuyến hoàn tất | 4.644 | 4.644 | bằng nhau |

Summary và comparison CSV/PNG được sinh trong `results/evaluation/` (thư mục kết quả được ignore bởi Git). Đây là một seed trên kịch bản nhu cầu lệch trục, không chứng minh fuzzy tốt hơn trong mọi điều kiện. Cần lặp lại nhiều seed và thêm benchmark cân bằng/bão hòa trước khi kết luận.

## Hợp đồng phối hợp đề xuất cho bốn người

1. **Control:** kết nối toàn bộ thành phần, đảm bảo hệ thống chạy được.
2. **SUMO:** Quản lý bản đồ ngã tư, thiết lập lưu lượng xe cộ chạy trên đường, và viết bảng giải thích rõ từng pha đèn ở mỗi bản đồ dùng để cho làn xe hướng nào đi
3. **Fuzzy:** giải thích được tại sao sửa như vậy và kỳ vọng nó giúp giảm kẹt xe bao nhiêu.
4. **Evaluation:** phân tích kết quả chạy, ra bảng thống kê, như role Data Analyst, việc như môn của thầy Phước.

Mỗi thay đổi model nên đi qua cùng hợp đồng: control cung cấp queue theo nhóm pha đã định nghĩa, fuzzy trả quyết định xanh, SUMO giữ logic chuyển pha an toàn, evaluation so sánh cùng scenario và seed.


## NOTE
Trong lúc làm nếu có chỗ cần thêm/sửa ở mục của người khác để chạy thì có thể sửa. Nhưng nhớ báo.