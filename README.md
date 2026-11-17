
```powershell
python -m pip install -r requirements.txt
```

Chạy GUI launcher:

```powershell
python control/launcher.py
```

Chạy thẳng bằng cmd:

```powershell
python control/run_sumo.py --scenario 4huong3lan --mode fuzzy --nogui --seed 1
python control/run_sumo.py --scenario 4huong2lan --mode fixed --green 30 --yellow 3 --nogui --seed 1
```

Có 3 chế độ: `observe` (mặc định), `fixed` (sửa tgian đè cố định), and `fuzzy`(luật mờ). mỗi run sẽ đc lưu kết quả vào `results/evaluation/`.

Dựng CSV so sánh với bảng:

```powershell
python -m evaluation.report_results
python -m evaluation.report_results --scenario 4huong3lan
python -m evaluation.report_results --scenario 4huong3lan --seed 1
```
