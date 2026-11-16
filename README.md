# Evaluation package

Thư mục này chứa các bước xử lý dữ liệu và so sánh hiệu suất giữa các chiến lược điều khiển giao thông.

## Luồng làm việc

1. Chạy mô phỏng SUMO để sinh ra file `tripinfo.xml`.
2. Chuyển `tripinfo.xml` thành CSV từng xe bằng `collect_metrics.py`.
3. Tính các chỉ số thống kê bằng `calculate_metrics.py`.
4. So sánh các chiến lược bằng `analyze_results.py`.
5. Vẽ biểu đồ bằng `plot_results.py`.

## Ví dụ chạy

```bash
"C:/Program Files/Python311/python.exe" evaluation/collect_metrics.py tripinfo.xml --output evaluation/results/tripinfo.csv
"C:/Program Files/Python311/python.exe" evaluation/calculate_metrics.py evaluation/results/tripinfo.csv --output evaluation/results/fixed_time_summary.csv --controller fixed_time --run-id fixed_time --simulation-duration 3600
"C:/Program Files/Python311/python.exe" evaluation/calculate_metrics.py evaluation/results/tripinfo.csv --output evaluation/results/fuzzy_summary.csv --controller fuzzy --run-id fuzzy --simulation-duration 3600
"C:/Program Files/Python311/python.exe" evaluation/analyze_results.py evaluation/results/fixed_time_summary.csv evaluation/results/fuzzy_summary.csv --output evaluation/results/comparison.csv
"C:/Program Files/Python311/python.exe" evaluation/plot_results.py evaluation/results/comparison.csv --output evaluation/results/plot.png
```

## Lưu ý

- Các file `tripinfo.xml` và `evaluation/results/*.csv` được sinh ra động trong quá trình chạy mô phỏng.
- Nếu dữ liệu đầu vào thiếu cột thời gian, script sẽ báo lỗi rõ ràng thay vì chạy ngầm.
- Khi cần so sánh nhiều hiệu ứng hơn, chỉ cần thêm summary CSV và dùng cùng `analyze_results.py`.
