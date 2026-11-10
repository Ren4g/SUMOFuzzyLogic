# Mô phỏng Ngã tư giao thông cơ bản 
Dự án này chứa các tệp cấu hình để chạy mô phỏng một ngã tư cơ bản bằng phần mềm Eclipse SUMO (Simulation of Urban MObility). Mô phỏng bao gồm mạng lưới đường 4 hướng, hệ thống đèn tín hiệu giao thông và các luồng phương tiện di chuyển liên tục.

## Cấu trúc thư mục

* **`intersection.net.xml`**: Tệp mạng lưới (Network). Chứa dữ liệu về cơ sở hạ tầng bao gồm các đoạn đường (edges), làn đường (lanes), vạch kẻ và hệ thống đèn tín hiệu giao thông tại ngã tư.
* **`routes.rou.xml`**: Tệp nhu cầu giao thông (Routes/Demand). Chứa định nghĩa về các tuyến đường và phương tiện. Tệp này sử dụng thẻ `<flow>` để tạo ra luồng xe chạy liên tục từ cả 4 hướng trong suốt 1000 bước thời gian mô phỏng, thay vì chỉ chạy một lượt.
* **`simulation.sumocfg`**: Tệp cấu hình tổng (Configuration). Đóng vai trò liên kết tệp mạng lưới và tệp phương tiện lại với nhau. Đây là tệp chính để khởi chạy trên giao diện SUMO.

## Yêu cầu phần mềm

* Đã cài đặt [Eclipse SUMO](https://eclipse.dev/sumo/) trên máy tính.

## Hướng dẫn chạy mô phỏng

1. Khởi động phần mềm **SUMO-GUI**.
2. Trên thanh menu, chọn **File** -> **Open Simulation...** (hoặc nhấn tổ hợp phím `Ctrl + O`).
3. Điều hướng đến thư mục project và chọn mở tệp `simulation.sumocfg`.
4. Trên thanh công cụ phía trên cùng, tìm mục **Delay** và chỉnh thông số lên khoảng **100ms đến 200ms**. Việc này giúp làm chậm tốc độ khung hình để bạn có thể dễ dàng quan sát xe chạy và đèn chuyển pha.
5. Nhấn nút **Run** (biểu tượng nút Play màu xanh lá) để bắt đầu.