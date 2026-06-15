# ĐẶC TẢ GIAO DIỆN VÀ LUỒNG NGƯỜI DÙNG (WIREFRAMES & UI FLOWS)
## DỰ ÁN: LEOPARD - HỆ THỐNG KẾT NỐI VẬN TẢI HÀNG HÓA TRỌNG TẢI LỚN

| Field | Value |
|---|---|
| **Tên tài liệu** | Wireframe & UI Flow Specification |
| **Dự án** | LEOPARD APP |
| **Phiên bản** | 1.0 |
| **Ngày tạo** | 2026-06-15 |
| **Tác giả** | UI/UX Designer & Tech Lead Team LEOPARD |
| **Trạng thái** | Approved / Single Source of Truth for Frontend |

---

## 1. TỔNG QUAN HỆ THỐNG GIAO DIỆN (UI OVERVIEW)

Hệ thống LEOPARD bao gồm 3 phân hệ giao diện chính được thiết kế để tương tác đồng bộ thời gian thực:
1. **Shipper Mobile App (Khách hàng):** Ứng dụng dành cho chủ hàng/SME chạy trên nền tảng Flutter (Android & iOS). Tập trung tối giản thao tác, hỗ trợ đặt đơn đa điểm nhanh, báo giá minh bạch và theo dõi xe thời gian thực.
2. **Driver Mobile App (Tài xế):** Ứng dụng dành cho tài xế xe tải/xe ba gác trên nền tảng Flutter (Android). Tập trung vào giao diện tương phản cao khi lái xe, dẫn đường chuyên biệt tránh cấm tải, cấm giờ và tối ưu hóa tuyến đường ghép hàng.
3. **Enterprise Web Portal & Admin Web (Doanh nghiệp & Admin):** Dashboard quản trị nền Web (Flutter Web) cho phép các Fleet Owner quản lý đội xe và Admin hệ thống duyệt hồ sơ, cấu hình giá cước.

### Sơ đồ luồng di chuyển chính (Core Navigation Flow)

```
[Khách hàng (Shipper)]
Đăng ký/Đăng nhập (OTP/Google) ──> Màn hình chính (Map & Điểm dừng)
                                            │
                                            ▼
                                   Nhập thông tin hàng hóa
                                            │
                                            ▼
                                  Chọn loại xe & Báo giá
                                            │
                                            ▼
                                   Thanh toán (VietQR)
                                            │
                                            ▼
                                  Theo dõi đơn real-time <── Chat/Gọi ẩn danh ──> [Tài xế (Driver)]
                                            │                                            ▲
                                            ▼                                            │
                                  Đánh giá & Hoàn tất                                    │
                                                                                         │
[Tài xế (Driver)]                                                                        │
Đăng ký/Đăng nhập (OTP) ──> Upload hồ sơ xe ──> Phê duyệt ──> Online ──> Nhận chuyến ────┘
                                                                 │
                                                                 ▼
                                                       Xem gợi ý đơn ghép (VRP)
```

---

## 2. SHIPPER APP UI (MOBILE)

### 2.1. Phân hệ Xác thực (Authentication)

#### Screen 2.1a: Đăng ký / Đăng nhập (Auth Selection)
*Màn hình chào mừng và chọn phương thức xác thực.*

```
+-----------------------------------+
|             LEOPARD               |
|       - Vận Tải Trọng Tải Lớn -   |
+-----------------------------------+
|                                   |
|             [ LOGO ]              |
|             LEOPARD               |
|                                   |
|  Chào mừng bạn đến với Leopard!   |
|  Giải pháp vận tải thông minh,    |
|  tránh cấm tải và tối ưu chi phí. |
|                                   |
|  +-----------------------------+  |
|  |  [+] Đăng nhập bằng Google  |  |
|  +-----------------------------+  |
|                                   |
|               - HOẶC -            |
|                                   |
|  Nhập số điện thoại của bạn:      |
|  [ +84 | 0987654321            ]  |
|                                   |
|  +-----------------------------+  |
|  |       TIẾP TỤC BẰNG SĐT     |  |
|  +-----------------------------+  |
|                                   |
|  Bằng cách tiếp tục, bạn đồng ý   |
|  với Điều khoản và Chính sách.    |
+-----------------------------------+
```
* **Mô tả luồng:**
  * Người dùng chọn **Đăng nhập bằng Google**: Hệ thống gọi Firebase Google Sign-In, tự động đăng nhập và đồng bộ profile. Nếu là tài khoản Driver mới đăng ký qua Google, hệ thống chuyển tiếp sang màn hình verify Số điện thoại.
  * Người dùng nhập **Số điện thoại** và nhấn **Tiếp tục**: Chuyển sang màn hình 2.1b để nhập mã OTP SMS.

#### Screen 2.1b: Xác thực mã OTP (OTP Verification)
*Màn hình nhập mã xác thực 6 chữ số gửi qua SMS.*

```
+-----------------------------------+
| < Quay lại                        |
+-----------------------------------+
|        XÁC THỰC SỐ ĐIỆN THOẠI     |
|                                   |
|  Mã OTP đã được gửi đến số:       |
|  +84 987 654 321                  |
|                                   |
|  Nhập mã gồm 6 chữ số:            |
|                                   |
|    [ 4 ] [ 8 ] [ 2 ] [ 0 ] [_] [_] |
|                                   |
|  Không nhận được mã?              |
|  Gửi lại mã sau (45s)             |
|                                   |
|  +-----------------------------+  |
|  |          XÁC NHẬN           |  |
|  +-----------------------------+  |
|                                   |
+-----------------------------------+
```
* **Quy tắc UI:**
  * Các ô nhập OTP tự động focus chuyển tiếp khi người dùng gõ số.
  * Cơ chế cooldown 60 giây hiển thị đếm ngược trước khi nút "Gửi lại mã" khả dụng.

---

### 2.2. Phân hệ Đặt đơn hàng (Booking Flow)

#### Screen 2.2a: Nhập điểm dừng đa điểm (Multi-stop Booking)
*Màn hình cho phép shipper nhập tối đa 5 điểm dừng và thông tin người nhận hàng.*

```
+-----------------------------------+
|  =  ĐẶT XE CHUYỂN HÀNG            |
+-----------------------------------+
|  [MAP VIEW - VIETMAP BACKGROUND]  |
|  (Hiển thị bản đồ vị trí hiện tại)|
|  * Marker A (Vị trí lấy hàng)     |
|  * Marker B (Điểm giao 1)         |
|  * Marker C (Điểm giao 2 - Đích)  |
+-----------------------------------+
|  ĐIỂM ĐÃ CHỌN:                    |
|  (A) Lấy hàng: 145 Điện Biên Phủ, |
|      Bình Thạnh, TP.HCM           |
|  (B) Giao 1: 56 Lê Lợi, Q.1       |
|      SĐT: 0901234567 (Nam)        |
|  (C) Giao 2: 789 Nguyễn Văn Linh, |
|      Quận 7, TP.HCM               |
|      SĐT: 0911888999 (Hoa)        |
|                                   |
|  [+] Thêm điểm dừng (Tối đa 5)    |
+-----------------------------------+
|  Chi tiết hàng hóa:               |
|  [ Vật liệu xây dựng (Sắt thép) ] |
|  Trọng lượng: [ 3,500   ] kg      |
|  Kích thước:  [ 4.5 ]x[ 2.0 ]x[ 1.8]m
|  [x] Cần xe có bửng nâng (lift gate)
|                                   |
|  +-----------------------------+  |
|  |     TÌM XE VÀ BÁO GIÁ       |  |
|  +-----------------------------+  |
+-----------------------------------+
```
* **Mô tả luồng:**
  * Địa chỉ sử dụng **Vietmap Autocomplete API** để gợi ý địa chỉ khi gõ.
  * Nút `[+] Thêm điểm dừng` sẽ chèn thêm một trường nhập địa chỉ và tự động đánh lại số thứ tự (A, B, C, D, E).
  * Checkbox "Cần xe có bửng nâng" sẽ kích hoạt bộ lọc loại trừ các xe không đáp ứng thuộc tính này trong DB.

#### Screen 2.2b: Lựa chọn loại xe và Báo giá động (Vehicle & Pricing Selection)
*Hiển thị danh sách các loại xe tải phù hợp kèm giá cước động tính từ hệ thống.*

```
+-----------------------------------+
| < Thay đổi địa điểm               |
+-----------------------------------+
|  LỘ TRÌNH DUYỆT: 18.5 km          |
|  Thời gian di chuyển dự kiến: 45p |
|                                   |
|  CHỌN LOẠI XE TẢI PHÙ HỢP:        |
|                                   |
|  ( ) Xe Ba Gác (Tối đa 1 tấn)     |
|      Giá: 250,000 VND             |
|                                   |
|  ( ) Xe Tải Nhỏ (< 2 tấn)         |
|      Giá: 450,000 VND             |
|                                   |
|  (*) Xe Tải Trung (2 - 5 tấn)     |
|      Giá: 850,000 VND  [Đề xuất]  |
|      - Sức tải tối đa: 5,000 kg   |
|      - Kích thước: 5.2x2.1x2.0m   |
|                                   |
|  ( ) Xe Tải Lớn (5 - 10 tấn)      |
|      Giá: 1,450,000 VND           |
|                                   |
|  Dịch vụ thêm:                    |
|  [x] Bốc xếp tại điểm lấy (+100k) |
|  [ ] Bốc xếp tại điểm giao (+100k) |
|                                   |
|  TỔNG CỘNG: 950,000 VND           |
|  +-----------------------------+  |
|  |       TIẾP TỤC ĐẶT XE       |  |
|  +-----------------------------+  |
+-----------------------------------+
```
* **Mô tả nghiệp vụ:**
  * Giá hiển thị là **Dynamic Price** được tính toán bởi backend dựa trên: Khoảng cách routing thực tế của Vietmap, loại xe, thời gian yêu cầu (giờ cao điểm) và phụ phí bốc xếp.
  * Các xe không đủ kích thước/tải trọng so với thông số hàng hóa nhập ở màn hình trước sẽ bị mờ đi (disable) kèm cảnh báo.

#### Screen 2.2c: Thanh toán VietQR Động (VietQR Payment)
*Hiển thị thông tin chuyển khoản ngân hàng tự động điền sẵn.*

```
+-----------------------------------+
| < Hủy đơn hàng                    |
+-----------------------------------+
|        XÁC NHẬN THANH TOÁN        |
|                                   |
|  Mã đơn hàng: LEOPARD-ORD9834     |
|  Số tiền: 950,000 VND             |
|                                   |
|        +-----------------+        |
|        |  #############  |        |
|        |  ##  VietQR   ##  |        |
|        |  ##  DYNAMIC  ##  |        |
|        |  ##  QR CODE  ##  |        |
|        |  #############  |        |
|        +-----------------+        |
|                                   |
|  Ngân hàng: MB Bank (Quân Đội)    |
|  Số tài khoản: 1900 8888 9999    |
|  Tên chủ TK: LEOPARD LOGISTICS   |
|  Nội dung CK: LEOPARD ORD9834     |
|                                   |
|  [ HƯỚNG DẪN QUÉT MÃ VIETQR ]     |
|  Vui lòng dùng ứng dụng ngân hàng |
|  quét mã QR trên để chuyển khoản  |
|  chính xác số tiền và nội dung.   |
|                                   |
|  +-----------------------------+  |
|  |   TÔI ĐÃ CHUYỂN KHOẢN XONG  |  |
|  +-----------------------------+  |
+-----------------------------------+
```
* **Tiêu chí AC:**
  * Mã QR được mã hóa theo chuẩn Napas VietQR chứa đầy đủ: BIN ngân hàng, Số tài khoản, số tiền và nội dung.
  * Khách hàng ấn "Tôi đã chuyển khoản xong", app sẽ hiển thị trạng thái chuyển tiếp chờ tài xế/hệ thống xác nhận và bắt đầu luồng tìm xe.

---

### 2.3. Phân hệ Theo dõi chuyến đi (Real-time Tracking)

#### Screen 2.3a: Bản đồ theo dõi thời gian thực (Real-time Tracking Map)
*Màn hình hiển thị vị trí tài xế di chuyển trên bản đồ và thông tin liên lạc.*

```
+-----------------------------------+
| Đơn hàng: LEOPARD-ORD9834         |
+-----------------------------------+
|                                   |
|    [A] Lấy hàng (Đã lấy)          |
|     |                             |
|    [🚚 Xe đang chạy...]           |
|     |                             |
|    [C] Điểm giao 2 (Đích)         |
|                                   |
|  [MAP VIEW - ROUTE POLYLINE ACTIVE]
|  - Marker A (Pickup)              |
|  - Marker C (Destination)         |
|  - Marker Truck (Realtime GPS)    |
|                                   |
+-----------------------------------+
|  Tài xế đang giao hàng            |
|  ETA dự kiến đến: 12 phút (10.2km)|
|                                   |
|  Tài xế: Nguyễn Văn Hùng          |
|  Xe: 29C-888.88 (Xe tải 3.5 tấn)  |
|  Đánh giá: 4.9* (124 chuyến)      |
|                                   |
|  +--------------+ +---------------+  |
|  |  📞 GỌI ĐIỆN | |  💬 CHAT (3)  |  |
|  +--------------+ +---------------+  |
+-----------------------------------+
```
* **Mô tả luồng:**
  * Marker Truck cập nhật vị trí mỗi 5 giây qua kết nối WebSocket.
  * Đồng hồ ETA đếm ngược (phút) được cập nhật động bằng mô hình AI XGBoost gửi từ backend.
  * Nút "GỌI ĐIỆN" kích hoạt luồng gọi ẩn danh che số điện thoại thật của hai bên.
  * Nút "CHAT" hiển thị số lượng tin nhắn chưa đọc từ tài xế. Nhấp vào mở màn hình chat (Screen 2.3b).

#### Screen 2.3b: Chat nhanh trong chuyến đi (In-app Chat Drawer)
*Giao diện chat real-time tích hợp trong chuyến đi.*

```
+-----------------------------------+
| < Quay lại Bản đồ                 |
+-----------------------------------+
|  Chat với Tài xế: Nguyễn Văn Hùng |
+-----------------------------------+
|  [14:10] Tài xế:                  |
|  Tôi đã đến điểm lấy hàng rồi ạ.  |
|                                   |
|  [14:11] Bạn (Shipper):           |
|  Dạ vâng, anh đợi em 5 phút xe    |
|  nâng đang đưa hàng ra nhé.       |
|                                   |
|  [14:12] Tài xế:                  |
|  Vâng ok bạn.                     |
|                                   |
|  [14:32] Tài xế: (Vừa gửi)        |
|  Hàng đã bốc xong, tôi bắt đầu di |
|  chuyển ra QL1A nhé.              |
|                                   |
+-----------------------------------+
|  [ Nhập tin nhắn...        ] [Gửi]|
+-----------------------------------+
```
* **Cơ chế hoạt động:**
  * Sử dụng kết nối WebSocket để đồng bộ tin nhắn ngay lập tức.
  * Lưu trữ lịch sử tin nhắn tại PostgreSQL cục bộ và tự động xóa sau 30 ngày kể từ khi hoàn tất chuyến đi để bảo mật thông tin.

---

## 3. DRIVER APP UI (MOBILE)

### 3.1. Phân hệ Hồ sơ tài xế (Driver Profile & Verification)

#### Screen 3.1a: Đăng ký thông tin và tải lên giấy tờ (Verification Queue)
*Màn hình hiển thị danh mục giấy tờ pháp lý cần thiết để tài xế hoạt động.*

```
+-----------------------------------+
|  HỒ SƠ TÀI XẾ                     |
+-----------------------------------+
|  Tài xế: Nguyễn Văn Hùng          |
|  Số điện thoại: 0987654321        |
|  Trạng thái hồ sơ: CHỜ DUYỆT      |
+-----------------------------------+
|  DANH SÁCH GIẤY TỜ BẮT BUỘC:      |
|                                   |
|  1. Giấy phép lái xe (GPLX)       |
|     Trạng thái: [ ĐÃ DUYỆT ✅ ]    |
|     Hạn dùng: 2030-12-31          |
|                                   |
|  2. Đăng kiểm xe (Kiểm định)      |
|     Trạng thái: [ YÊU CẦU LẠI ❌ ] |
|     Lý do: Ảnh chụp mờ số khung,  |
|            yêu cầu chụp lại.      |
|     [ CHỤP ẢNH LẠI / TẢI LÊN ]    |
|                                   |
|  3. Bảo hiểm dân sự xe tải        |
|     Trạng thái: [ CHƯA CÓ ⚠️ ]    |
|     [ CHỤP ẢNH / TẢI LÊN ]        |
|                                   |
|  4. Cà-vẹt xe (Đăng ký xe)        |
|     Trạng thái: [ CHỜ DUYỆT ⏳ ]   |
+-----------------------------------+
|  Lưu ý: Hồ sơ của bạn cần được    |
|  Admin phê duyệt đầy đủ để có thể |
|  bật Online nhận đơn hàng.        |
+-----------------------------------+
```
* **Quy tắc UI:**
  * Nút "CHỤP ẢNH / TẢI LÊN" mở camera điện thoại hoặc thư viện ảnh.
  * Chỉ hiển thị nút "Bật Online" khi tất cả các mục giấy tờ chuyển sang trạng thái "ĐÃ DUYỆT ✅".

---

### 3.2. Phân hệ Định tuyến & Dẫn đường (Trip Navigation)

#### Screen 3.2a: Bản đồ dẫn đường Truck-Friendly (Navigation Screen)
*Màn hình bản đồ có chỉ dẫn chi tiết, cảnh báo cấm tải trọng/chiều cao và hỗ trợ offline.*

```
+-----------------------------------+
| [!] CẢNH BÁO: PHÍA TRƯỚC CÓ CẦU   |
|     GIỚI HẠN CHIỀU CAO 3.5M       |
+-----------------------------------+
|     Rẽ Trái vào đường QL1A        |
|     Sau 250 mét                   |
+-----------------------------------+
|                                   |
|  [MAP VIEW - TRUCK ROUTING ACTIVE] |
|   * Cầu thấp 3.5m (Biểu tượng đỏ) |
|   * Route tránh đi vòng đường gom |
|   * Vị trí hiện tại của xe tải    |
|                                   |
+-----------------------------------+
|  ĐANG CHẠY: ĐIỂM GIAO 2           |
|  Tải trọng xe của bạn: 5.0 tấn    |
|  Chiều cao xe: 3.2 mét            |
|                                   |
|  Quãng đường còn lại: 4.8 km      |
|  Thời gian dự kiến: 8 phút        |
|                                   |
|  +-----------------------------+  |
|  |     ĐÃ ĐẾN ĐIỂM GIAO HÀNG   |  |
|  +-----------------------------+  |
|  [!] Offline Mode: Đang lưu GPS   |
+-----------------------------------+
```
* **Mô tả nghiệp vụ:**
  * Bản đồ hiển thị tuyến đường đã được lọc qua API **Vietmap Routing Truck Profile** để tránh cầu thấp và đường cấm tải trọng tương ứng với xe của tài xế (Xe 5.0 tấn, cao 3.2m).
  * Banner cảnh báo màu đỏ xuất hiện ở trên cùng khi xe chuẩn bị đến gần khu vực giới hạn chiều cao hoặc cấm giờ.
  * Dưới cùng hiển thị cảnh báo `[!] Offline Mode` nếu phát hiện thiết bị mất kết nối mạng. App sẽ tự động ghi tọa độ GPS vào bộ nhớ đệm (SQLite/Hive) và đồng bộ lại lên server khi có mạng.

---

### 3.3. Phân hệ Tối ưu hóa ghép đơn (VRP Optimization Bids)

#### Screen 3.3a: Gợi ý ghép đơn trên đường về (VRP Return Match Notification)
*Cửa sổ popup tự động gợi ý đơn hàng ghép dọc đường về để tối ưu chi phí.*

```
+-----------------------------------+
|         CÓ ĐƠN HÀNG GHÉP MỚI!     |
|   (Tối ưu tuyến đường về của bạn)  |
+-----------------------------------+
|  Hệ thống tìm thấy 1 đơn hàng     |
|  nằm trên lộ trình quay về TP.HCM |
|                                   |
|  * Nơi nhận: Kho Tân Uyên, Bình D.|
|    (Cách vị trí hiện tại: 2.5 km) |
|  * Nơi giao: Quận Bình Thạnh, HCM |
|                                   |
|  Thông số đơn ghép:               |
|  - Hàng hóa: Thùng carton (350kg)  |
|  - Đi chệch hướng thêm: +1.8 km   |
|                                   |
|  DOANH THU CỘNG THÊM:             |
|  +320,000 VND                     |
|                                   |
|  Thời gian suy nghĩ còn lại:      |
|             [ 18 giây ]           |
|                                   |
|  +-----------------------------+  |
|  |         CHẤP NHẬN GHÉP      |  |
|  +-----------------------------+  |
|  |             BỎ QUA          |  |
|  +-----------------------------+  |
+-----------------------------------+
```
* **Quy tắc Nghiệp vụ:**
  * Popup tự động kích hoạt nhờ thuật toán **Google OR-Tools VRP** chạy ngầm ở backend (Celery task) phân tích khoảng cách và tải trọng trống của xe.
  * Tài xế có đúng 30 giây để nhấn "CHẤP NHẬN GHÉP". Nếu quá thời gian, popup tự đóng và chuyển đơn hàng cho tài xế khác trong khu vực.

---

## 4. ENTERPRISE PORTAL & ADMIN WEB (DASHBOARD)

*Giao diện Web được thiết kế theo tỷ lệ màn hình ngang lớn (Desktop Layout, chiều rộng mô phỏng ~80 ký tự).*

### 4.1. Phân hệ Doanh nghiệp vận tải (Fleet Owner Dashboard)
*Bảng điều khiển cho phép chủ doanh nghiệp theo dõi toàn bộ đội xe, doanh thu và đối soát thanh toán.*

```
+-------------------------------------------------------------------------------+
|  LEOPARD  [Đội xe: Kim Anh Logistics]               Admin: kima-log@gmail.com |
+-------------------------------------------------------------------------------+
|  [Tổng quan]  [Bản đồ Đội xe]  [Tài xế]  [Phương tiện]  [Đơn hàng]  [Đối soát] |
+-------------------------------------------------------------------------------+
|  THỐNG KÊ ĐỘI XE HÔM NAY:                                                      |
|  +-------------------+  +-------------------+  +-------------------+          |
|  | Xe đang chạy: 12  |  | Xe đang rảnh: 3   |  | Doanh thu ngày:   |          |
|  | Hiệu suất: 80%    |  | Trực tuyến: 15    |  | 18,450,000 VND    |          |
|  +-------------------+  +-------------------+  +-------------------+          |
|                                                                               |
|  BẢN ĐỒ ĐỘI XE THỜI GIAN THỰC:                                                |
|  +-------------------------------------------------------------------------+  |
|  |  [ MAP VIEW - SHOWING ALL VEHICLE MARKERS IN REAL-TIME ]                |  |
|  |  - Xe 29C-111.11 (Đang chạy - Đơn ORD882)                               |  |
|  |  - Xe 51D-222.22 (Đang rảnh - Bình Dương)                                |  |
|  |  - Xe 29C-333.33 (Mất tín hiệu 10 phút trước - Cần kiểm tra)            |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  DANH SÁCH ĐƠN CHỜ PHÂN XE (HỢP ĐỒNG DOANH NGHIỆP):                           |
|  +--------+---------------+--------------------+-------------+-------------+  |
|  | Mã Đơn | Điểm Lấy      | Điểm Giao          | Trọng Tải   | Hành động   |  |
|  +--------+---------------+--------------------+-------------+-------------+  |
|  | ORD990 | Kho Sóng Thần | Cảng Cát Lái, Q.2  | 15 Tấn      | [ Gán Xe ]  |  |
|  | ORD992 | Dĩ An, BD     | Q.Thủ Đức, TP.HCM  | 5 Tấn       | [ Gán Xe ]  |  |
|  +--------+---------------+--------------------+-------------+-------------+  |
|                                                                               |
|  BÁO CÁO ĐỐI SOÁT ĐỊNH KỲ THÁNG 6/2026:                                       |
|  - Tổng số chuyến đã giao: 145 chuyến                                         |
|  - Tổng tiền cước: 124,500,000 VND                                            |
|  - Chiết khấu nền tảng LEOPARD (5%): 6,225,000 VND                            |
|  - Số dư cần thanh toán trước ngày 05/07: 118,275,000 VND [ Thanh toán ngay ] |
+-------------------------------------------------------------------------------+
```

---

### 4.2. Phân hệ Quản trị hệ thống (Admin Portal)
*Trang quản lý dành cho quản trị viên hệ thống để kiểm duyệt tài liệu tài xế và cấu hình giá.*

```
+-------------------------------------------------------------------------------+
|  LEOPARD SYSTEM ADMIN                                     Chào, Admin Minh    |
+-------------------------------------------------------------------------------+
|  [Duyệt Hồ Sơ (3)]  [Quản Lý Người Dùng]  [Quản Lý Đơn]  [Cấu Hình Cước Phí]  |
+-------------------------------------------------------------------------------+
|  HÀNG CHỜ DUYỆT HỒ SƠ TÀI XẾ:                                                 |
|  +-------------+----------------+--------------------+---------------------+  |
|  | Tên Tài Xế  | Số Điện Thoại  | Loại Phương Tiện   | Giấy Tờ Cần Duyệt   |  |
|  +-------------+----------------+--------------------+---------------------+  |
|  | Nguyễn Văn A| 0905123456     | Xe tải 8 tấn       | Đăng kiểm, Cà-vẹt   |  |
|  | Trần Văn B  | 0914888999     | Xe container       | GPLX Hạng FC        |  |
|  +-------------+----------------+--------------------+---------------------+  |
|                                                                               |
|  CHI TIẾT DUYỆT HỒ SƠ: TÀI XẾ NGUYỄN VĂN A                                    |
|  +------------------------------------+------------------------------------+  |
|  | 📷 ẢNH CHỤP GIẤY ĐĂNG KIỂM XE      | THÔNG TIN KHAI BÁO:                |  |
|  | +--------------------------------+ | - Biển số xe: 29C-999.99           |  |
|  | |                                | | - Số khung: RLHA10293848        |  |
|  | |          [ PHOTO ]             | | - Hạn kiểm định: 2026-12-15       |  |
|  | |                                | |                                    |  |
|  | +--------------------------------+ | [ DUYỆT THÔNG TIN ]  [ TỪ CHỐI ]   |  |
|  +------------------------------------+------------------------------------+  |
|                                                                               |
|  CẤU HÌNH BẢNG GIÁ CƯỚC DỰA TRÊN KHOẢNG CÁCH VÀ TẢI TRỌNG (DYNAMIC PRICING):   |
|  - Giá mở cửa (0-2 km):      [ 50,000 ] VND (Xe ba gác) | [ 150,000 ] (Xe 5t) |
|  - Giá mỗi km tiếp theo:     [ 12,000 ] VND (Xe ba gác) | [  22,000 ] (Xe 5t) |
|  - Hệ số giờ cao điểm (16-19h):  [ 1.25 ]                                     |
|  - Hệ số thời tiết mưa bão:      [ 1.15 ]                                     |
|                                                              [ CẬP NHẬT BẢNG GIÁ ]
+-------------------------------------------------------------------------------+
```

---

## 5. MA TRẬN PHÂN QUYỀN TRUY CẬP MÀN HÌNH (SCREEN ACCESS MATRIX)

Dưới đây là ma trận phân quyền các chức năng tương ứng với từng màn hình được định nghĩa ở trên:

| Phân hệ màn hình | Guest | Shipper | Driver | Fleet Owner | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| **Auth & OTP (2.1a, 2.1b)** | **Có** | Không | Không | Không | Không |
| **Booking & Báo Giá (2.2a, 2.2b)** | Không | **Có** | Không | **Có** | Không |
| **Thanh toán VietQR (2.2c)** | Không | **Có** | Không | **Có** | Không |
| **Theo dõi & Chat (2.3a, 2.3b)** | Không | **Có** | **Có** | **Có** | **Có** |
| **Hồ sơ tài xế (3.1a)** | Không | Không | **Có** | **Có** | Không |
| **Dẫn đường & Bản đồ (3.2a)** | Không | Không | **Có** | Không | Không |
| **Ghép đơn VRP (3.3a)** | Không | Không | **Có** | Không | Không |
| **Dashboard Đội xe (4.1)** | Không | Không | Không | **Có** | **Có** |
| **Duyệt Hồ Sơ & Cấu Hình (4.2)** | Không | Không | Không | Không | **Có** |

---

## 6. KHẢ NĂNG OFFLINE VÀ BỘ NHỚ ĐỆM (OFFLINE STORAGE SPECS)

Để đối phó với tình trạng mất sóng dọc đường (đèo dốc, quốc lộ vùng sâu vùng xa), luồng thiết bị của tài xế được quy định như sau:

```
                  ┌───────────────────────────────┐
                  │    Tài xế đang di chuyển     │
                  └──────────────┬────────────────┘
                                 │
                        [Có kết nối mạng?]
                           /          \
                       (Có)          (Không)
                       /                \
     ┌────────────────▼────────┐  ┌──────▼──────────────────┐
     │ Gửi GPS trực tiếp lên   │  │ Lưu GPS vào Hive/SQLite │
     │ WebSocket backend       │  │ local DB. Hiển thị      │
     │                         │  │ cảnh báo "Offline"      │
     └─────────────────────────┘  └──────────────┬──────────┘
                                                 │
                                         [Có mạng trở lại]
                                                 │
                                                 ▼
                                  ┌─────────────────────────┐
                                  │ Sync toàn bộ tọa độ đã  │
                                  │ lưu lên API `/sync-gps` │
                                  └─────────────────────────┘
```

* **Ràng buộc lưu trữ cục bộ (Local Caching):**
  * Tối đa 500 tọa độ GPS (~40 phút di chuyển không mạng) được lưu trữ. Sau khi đầy, hệ thống ghi đè các tọa độ cũ nhất để tránh phân mảnh bộ nhớ.
  * Lịch trình chuyển đi hiện tại và thông tin người nhận hàng được mã hóa và lưu tại Hive Storage để tài xế có thể xem offline bất cứ lúc nào.
