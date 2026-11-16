launcher.py (cửa sổ chọn thông số)
   │  bấm "Chạy" → gọi run_sumo.py kèm tham số
   ▼
run_sumo.py
   │  traci.start()  → bật SUMO, nối kết nối
   │  vòng lặp: bước 1, bước 2, ... (đọc số liệu, đổi đèn nếu cần)
   │  traci.close()  → tắt SUMO
   │  đọc kết quả, ghi vào results/
   ▼
results/results.csv + tripinfo_*.xml