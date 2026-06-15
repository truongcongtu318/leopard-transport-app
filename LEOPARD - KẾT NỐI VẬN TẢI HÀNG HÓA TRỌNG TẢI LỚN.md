## **PROJECT PRD - LEOPARD APP** 

## **1. TỔNG QUAN DỰ ÁN** 

**Tên dự án:** LEOPARD 

**Mục tiêu:** Xây dựng App demo 

**Ngân sách tối đa:** 15.000.000 VND (không phát sinh thêm) 

**Thời gian triển khai kỳ vọng:** Có sản phẩm trước 15/9/2026 

## **2. PHÂN TÍCH THỊ TRƯỜNG & ĐỐI TƯỢNG** 

**Đối tượng người dùng mục tiêu:** 

- **Doanh nghiệp SME** ( Cửa hàng vật liệu xây dựng, nội thất, máy móc, nông sản, siêu thị mini, xưởng sản xuất,...). 

- **Chuyển nhà / Chuyển văn phòng** : Gia đình, sinh viên (hàng cồng kềnh), công ty. 

- **Xây dựng & Công trình** : Vận chuyển xi măng, sắt thép, thiết bị nhỏ,... 

- **Nông sản & Thực phẩm** : Chở số lượng lớn trong nội thành, từ ngoại thành vào thành phố hoặc ngược lại 

- **Tài xế** : Chủ xe ba gác, xe tải freelance hoặc đội xe nhỏ 

**Nỗi đau của thị trường:** Cần một app chuyên sâu cho việc vận chuyển hàng vừa và nhỏ dành cho xe tải/xe ba gác 

**Giải pháp của Leopard:** Ứng dụng tập trung vào sự tinh gọn, tốc độ tải trang nhanh và giao diện dễ thao tác, không có tính năng thừa. 

## **3. DANH SÁCH TÍNH NĂNG CHI TIẾT** 

|**STT**|**Tính năng**|**Mô tả chi tiết (Description)**|**Mức độ ưu tiên**|
|---|---|---|---|
|**1**|**Đăng ký / Đăng**<br>**nhập**|Đăng ký qua Số điện thoại/email.<br>Có xác thực tài khoản bằng các loại<br>giấy tờ hợp lệ.<br>Đăng nhập nhanh qua Google|Bắt buộc|



|||||||
|---|---|---|---|---|---|
||**2**|**Quản lý Hồ sơ**|Cho phép người dùng cập nhật Họ|Bắt buộc||
|||**cá nhân**|tên, Ảnh đại diện, Số điện thoại,|||
||||email, giấy phép lái xe, cà vẹt xe,...|||
||||và các giấy tờ liên quan khác theo|||
||||quy định của pháp luật.|||
||**3**|**Tính năng cốt**||**Bắt buộc**||
|||**lõi**|-**Đặt đơn nhanh qua app:**Vị trí<br>lấy/giao (đa điểm), ảnh/video hàng|||
||||hóa, kích thước/trọng lượng, yêu|||
||||cầu bốc xếp, số điện thoại liên hệ|||
||||của 2 bên (khách hàng và tài xế).|||
||||**- AI dự báo ETA chính xác**:|||
||||XGBoost + traffic real-time|||
||||Vietmap/Google + thời tiết|||
||||**- Tối ưu ghép hàng & tuyến**|||
||||**đường:**OR-Tools VRP → giảm|||
||||chạy rỗng về sau khi tài xế đã hoàn|||
||||thành cuốc xe.|||
||||-**Navigation truck-friendly:**tránh|||
||||cấm tải, cầu thấp, giờ cấm, đèn đỏ,|||
||||ket xe.|||
||||-**Theo dõi real-time:**Lộ trình di|||
||||chuyển của xe khi nhận và giao|||
||||hàng, gọi điện, nhắn tin, chứng minh|||
||||giao hàng bằng ảnh.|||
||||-**Thanh toán:**Chuyển khoản,|||
||||COD, hóa đơn VAT tự động.|||
||||-**Gói doanh nghiệp:**Hợp đồng|||
||||định kỳ, dashboard quản lý fleet.|||
|||||||



|**4**|**Tìm kiếm / Bộ**<br>**lọc cơ bản**|Tìm kiếm theo từ khóa chính hoặc<br>lọc theo danh mục đơn giản.|Bắt buộc|
|---|---|---|---|
|**5**|**Thông báo**<br>**(Notifications)**|Sử dụng thông báo trong app<br>(In-app) hoặc đẩy qua Firebase<br>Cloud Messaging (Miễn phí).|Trung bình|
|**6**|**Tích hợp thanh**<br>**toán**|**- Chuyển khoản:**Giai đoạn này chỉ<br>cần hiển thị**Mã QR chuyển khoản**<br>**ngân hàng (VietQR)**để người dùng<br>quét mã.<br>_Không tích hợp cổng thanh toán_<br>_phức tạp (như Momo, VNPay) vì tốn_<br>_phí và thời gian duyệt hồ sơ pháp lý._<br>**- Tiền mặt:**Chấp nhận với các đơn<br>hàng nhỏ >500.000 VNĐ hoặc các<br>đơn dưới 5km|Bắt buộc|



## **4. YÊU CẦU VỀ GIAO DIỆN & TRẢI NGHIỆM** 

**Thiết kế:** Có thể tham khảo ví dụ dưới đây 

**Giao diện:** Tối giản, sử dụng các màu chủ đạo (Trắng, vàng, xanh biển, xanh lá pastel như hình). Tốc độ phản hồi của giao diện phải mượt mà trên thiết bị di động/web. 

## **5. TIÊU CHÍ NGHIỆM THU & BÀN GIAO** 

**Mã nguồn (Source Code):** Bàn giao toàn bộ source code sạch, có comment cơ bản và được lưu trữ trên GitHub/GitLab. 

**Tài liệu hướng dẫn (Documentation):** Tài liệu ngắn gọn hướng dẫn cách deploy (triển khai) app lên server/hosting và cách cấu hình các tài khoản liên quan (Firebase, Domain). 

**Sản phẩm chạy được (Live Product):** App phải chạy ổn định trên môi trường production, không có lỗi nghiêm trọng (Crash/Freeze) ở các tính năng cốt lõi. 

**Bảo hành/Hỗ trợ:** Hỗ trợ sửa lỗi (Bug fix) phát sinh trong vòng ít nhất 1 - 3 tháng sau khi bàn giao. 

**Báo cáo quá trình thực hiện:** Đầy đủ và chi tiết, bao gồm tất cả data khi tiến hành train app, thu thập insight, hình ảnh cập nhật tiến độ,... 

