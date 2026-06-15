# KẾ HOẠCH PHÂN CHIA NHIỆM VỤ VÀ PHÂN LẬP KIẾN TRÚC (TASK ALLOCATION & ARCHITECTURAL BOUNDARIES)
## DỰ ÁN: LEOPARD - HỆ THỐNG KẾT NỐI VẬN TẢI HÀNG HÓA TRỌNG TẢI LỚN

| Field | Value |
|---|---|
| **Tên tài liệu** | Phân chia nhiệm vụ tránh chồng chéo khi đồng phát triển (Co-dev) |
| **Dự án** | LEOPARD APP |
| **Phiên bản** | 1.0 |
| **Ngày tạo** | 2026-06-15 |
| **Tác giả** | Tech Lead & PM Team LEOPARD |
| **Đối tượng áp dụng** | Dev A (Backend & AI), Dev B (Frontend & Mobile/Web) |

---

## 1. NGUYÊN TẮC PHÂN LẬP KIẾN TRÚC (ARCHITECTURAL BOUNDARIES)
Để ngăn chặn hoàn toàn việc xung đột mã nguồn (Git merge conflicts) và xung đột luồng xử lý dữ liệu khi có sự tham gia của các **AI Agent** (vốn có xu hướng chỉnh sửa file rất nhanh), dự án áp dụng quy tắc phân lập thư mục và quyền ghi như sau:

### 1.1. Phân chia quyền ghi thư mục tuyệt đối (Directory Ownership)
```
[Hành động]   [Phạm vi thư mục]                 [Owner duy nhất được phép Merge/Push]
WRITE/EDIT -> /backend/                          -> Dev A (Backend & AI)
WRITE/EDIT -> /frontend/                         -> Dev B (Frontend & Mobile)
WRITE/EDIT -> /docs/api-contract.md              -> Cả hai (Phải thống nhất trước khi code)
WRITE/EDIT -> /docs/erd.md                       -> Dev A (Backend)
WRITE/EDIT -> /docker-compose.yml, /scripts/     -> Dev A (Backend)
WRITE/EDIT -> /.github/workflows/                -> Dev A (Backend)
```
* **Quy tắc vàng:** Dev B **tuyệt đối không** chỉnh sửa bất kỳ file nào trong `/backend` (kể cả requirements.txt). Dev A **tuyệt đối không** chỉnh sửa file trong `/frontend` (kể cả pubspec.yaml). AI Agent của mỗi người chỉ được hoạt động trong phân vùng thư mục của người đó.

### 1.2. Phân chia quyền hạn Cơ sở dữ liệu (Database Schema Ownership)
Khi làm việc với PostgreSQL, việc thay đổi bảng (add column, change type) dễ dẫn đến lỗi crash app của Frontend nếu không đồng bộ.
* **Quy tắc thay đổi DB:**
  1. Dev A là **Database Owner duy nhất**. Chỉ Dev A được phép chỉnh sửa `/docs/erd.md` và viết các file migration (Alembic).
  2. Nếu Dev B phát hiện UI cần thêm trường thông tin (ví dụ: bảng `users` cần thêm cột `nickname`):
     * Dev B tạo một **Git Issue** hoặc yêu cầu trực tiếp Dev A.
     * Dev A thực hiện tạo migration `alembic revision --autogenerate`, kiểm tra tính tương thích ngược, update schema tài liệu, và push lên branch `dev`.
     * Dev B pull code mới về, chạy `docker compose down -v && docker compose up -d` để reload database local sạch.

---

## 2. QUY TRÌNH PHÁT TRIỂN SONG SONG (MOCK-FIRST WORKFLOW)
Để Dev B có thể code giao diện và logic Flutter liên tục mà không cần đợi Dev A viết xong API thật, team áp dụng quy trình **Mock-First**:

1. **Thống nhất Contract:** Hai bên đồng duyệt Endpoint và Schema trong `docs/api-contract.md`.
2. **Tạo Mock Data:** Dev B cấu hình HTTP Client (Dio) trong Flutter để tự động trả về mock data (hardcoded JSON tương ứng với API Contract) khi gọi API local.
3. **Phát triển độc lập:**
   * Dev A: Viết code Backend thật, test endpoint qua Swagger UI (`http://localhost:8000/docs`).
   * Dev B: Code giao diện và logic state Flutter dựa trên dữ liệu Mock.
4. **Hợp nhất (Integration):** Khi Dev A thông báo endpoint đã sẵn sàng trên server dev/local, Dev B chỉ cần tắt chế độ Mock của Dio để trỏ request tới Backend thật.

---

## 3. BẢNG PHÂN CHIA NHIỆM VỤ CHI TIẾT (WBS) - KHÔNG CHỒNG CHÉO

Dưới đây là ma trận phân rã công việc (Work Breakdown Structure) chi tiết cho từng phân hệ, phân định rõ ranh giới bàn giao (Hand-off points) và Tiêu chí nghiệm thu (DoD) riêng cho từng người:

### 3.1. Phân hệ 1: Đăng ký & Xác thực (Auth & Profile)
* **API Contract thống nhất:** `/auth/phone/otp-request`, `/auth/phone/otp-verify`, `/auth/google`

| Vai trò | Nhiệm vụ chi tiết | Output phân lập | Định nghĩa hoàn thành (DoD) |
|---|---|---|---|
| **Dev A (Backend)** | - Viết API nhận mã Token từ Client, verify với Firebase Admin SDK.<br>- Tạo session JWT Token (AccessToken, RefreshToken).<br>- Tạo user mới trong DB PostgreSQL nếu là số điện thoại mới.<br>- Viết API GET/PUT `/users/profile`. | - File: `/backend/app/api/v1/auth.py`<br>- File: `/backend/app/models/user.py` | - Test coverage API Auth đạt > 85% (Pytest).<br>- Trả về đúng mã code HTTP 200/201 và JSON token schema. |
| **Dev B (Frontend)** | - Thiết kế giao diện (UI) OTP SMS và Google Sign-in.<br>- Tích hợp Firebase Auth SDK Client phía Flutter.<br>- Gọi API `/auth/verify` gửi Firebase Token lên backend.<br>- Lưu trữ AccessToken vào Flutter Secure Storage. | - Thư mục: `/frontend/lib/features/auth/`<br>- State management: `AuthBloc` | - Đăng nhập nhận OTP SMS và chuyển màn hình thành công trên Emulator.<br>- Giao diện responsive trên Web và Mobile. |

### 3.2. Phân hệ 2: Quản lý Giấy tờ tài xế (Driver Documents Verification)
* **API Contract thống nhất:** `POST /drivers/documents`, `GET /drivers/documents/status`

| Vai trò | Nhiệm vụ chi tiết | Output phân lập | Định nghĩa hoàn thành (DoD) |
|---|---|---|---|
| **Dev A (Backend)** | - Viết service lưu trữ file upload lên ổ đĩa local (`/uploads`).<br>- Viết API nhận ảnh giấy tờ (GPLX, đăng kiểm...) từ Multipart Form.<br>- Tạo bản ghi trạng thái giấy tờ `pending` trong DB.<br>- Viết API phê duyệt/từ chối tài liệu (chỉ dành cho Admin). | - File: `/backend/app/api/v1/drivers.py`<br>- Thư mục lưu file: `/backend/uploads/` | - Trả về link ảnh hợp lệ sau khi upload.<br>- Cập nhật đúng trạng thái duyệt trong PostgreSQL. |
| **Dev B (Frontend)** | - Code màn hình chụp và chọn ảnh từ thư viện (dùng `image_picker`).<br>- Code màn hình xem trạng thái phê duyệt (Pending/Approved/Rejected).<br>- Tích hợp API gửi file ảnh lên Backend qua Multipart Request (Dio). | - Thư mục: `/frontend/lib/features/auth/presentation/widgets/`<br>- UI: `DocumentUploadPage` | - Người dùng chọn ảnh, gửi yêu cầu upload thành công và hiển thị thanh tiến trình loading (Progress Bar). |

### 3.3. Phân hệ 3: Đặt đơn đa điểm & Tối ưu hóa tuyến đường (Booking & VRP Route)
* **API Contract thống nhất:** `POST /bookings/optimize` (OR-Tools VRP Matrix), `POST /bookings/create`

| Vai trò | Nhiệm vụ chi tiết | Output phân lập | Định nghĩa hoàn thành (DoD) |
|---|---|---|---|
| **Dev A (Backend)** | - Nhận tọa độ GPS các Stop từ request.<br>- Gọi OSRM local sinh ma trận khoảng cách.<br>- Chuyển ma trận vào giải thuật Google OR-Tools VRP để sắp xếp thứ tự giao hàng tối ưu.<br>- Trả về danh sách stop đã sắp xếp kèm tọa độ đường vẽ (polyline). | - File: `/backend/app/workers/vrp_solver.py`<br>- File: `/backend/app/services/vietmap.py` | - Giải thuật VRP xử lý thành công ma trận 10 điểm giao trong < 1.5 giây.<br>- Không bị lặp điểm. |
| **Dev B (Frontend)** | - Thiết kế màn hình bản đồ chọn nhiều điểm dừng giao hàng.<br>- Cho phép kéo thả thay đổi vị trí các điểm dừng trên UI.<br>- Gửi danh sách điểm dừng lên API `/bookings/optimize` để nhận chuỗi điểm tối ưu.<br>- Vẽ polyline tuyến đường tối ưu lên bản đồ. | - Thư mục: `/frontend/lib/features/booking/`<br>- Widget: `MultiStopMapWidget` | - Người dùng chọn 5 điểm dừng, bản đồ vẽ đúng tuyến đường nối các điểm sau khi nhận kết quả tối ưu từ backend. |

### 3.4. Phân hệ 4: Theo dõi thời gian thực (Real-time Tracking & GPS)
* **API Contract thống nhất:** WS `wss://api.leopard.vn/ws/v1/orders/{order_id}/track`

| Vai trò | Nhiệm vụ chi tiết | Output phân lập | Định nghĩa hoàn thành (DoD) |
|---|---|---|---|
| **Dev A (Backend)** | - Xây dựng WebSocket Server bằng FastAPI.<br>- Setup Redis Pub/Sub: Driver push tọa độ GPS lên kênh Redis -> WebSocket phát tọa độ đó cho Shipper đang sub kênh.<br>- Viết trigger lưu tọa độ vào bảng `gps_tracking` (TimescaleDB) cách mỗi 10 giây. | - File: `/backend/app/api/v1/websocket.py`<br>- Cấu hình Redis Pub/Sub | - WebSocket giữ kết nối ổn định.<br>- Log ghi nhận tọa độ GPS liên tục mà không làm tăng nghẽn DB nhờ TimescaleDB hypertable. |
| **Dev B (Frontend)** | - Tích hợp WebSocket Client kết nối đến server Backend.<br>- Lắng nghe tọa độ GPS nhận được.<br>- Cập nhật tọa độ Marker xe trên bản đồ bằng cách nội suy (Lerp) góc xoay và tọa độ để marker di chuyển mượt mà.<br>- Xử lý reconnection tự động khi mất sóng mạng 4G. | - Thư mục: `/frontend/lib/features/tracking/`<br>- State: `TrackingCubit` | - Marker xe tải di chuyển mượt trên bản đồ theo chu kỳ nhận dữ liệu.<br>- Tự động phục hồi kết nối WS sau < 5 giây nếu mạng bị ngắt. |

### 3.5. Phân hệ 5: AI ETA Prediction
* **API Contract thống nhất:** `POST /eta/predict`

| Vai trò | Nhiệm vụ chi tiết | Output phân lập | Định nghĩa hoàn thành (DoD) |
|---|---|---|---|
| **Dev A (Backend)** | - Tải mô hình XGBoost Regressor đã train.<br>- Khi nhận request, gọi API OpenWeather lấy trạng thái thời tiết tại điểm lấy hàng.<br>- Nạp đặc trưng (Thời tiết, Khoảng cách từ OSRM, Giờ cao điểm, Tải trọng xe) vào mô hình để dự báo ETA.<br>- Trả về số phút dự kiến giao hàng. | - File: `/backend/app/ml/model.py`<br>- File: `/backend/app/services/weather.py` | - Thời gian suy luận (Inference time) của model < 100ms.<br>- Sai số MAE (Mean Absolute Error) kiểm thử offline < 5 phút. |
| **Dev B (Frontend)** | - Code UI hiển thị thời gian ETA đếm ngược của đơn hàng.<br>- Hiển thị icon thời tiết thực tế nhận từ Backend API (ví dụ: mưa to -> hiển thị cảnh báo giao chậm). | - Thư mục: `/frontend/lib/features/tracking/presentation/widgets/`<br>- UI: `EtaCountdownWidget` | - Màn hình tracking hiển thị đúng thời gian đếm ngược cập nhật trực tiếp từ Backend API. |

### 3.6. Phân hệ 6: Thanh toán VietQR & Đối soát
* **API Contract thống nhất:** `POST /billing/payments/vietqr`, `POST /billing/webhook/payos` (hoặc VietQR callback)

| Vai trò | Nhiệm vụ chi tiết | Output phân lập | Định nghĩa hoàn thành (DoD) |
|---|---|---|---|
| **Dev A (Backend)** | - Tính toán giá cước đơn hàng dựa trên khoảng cách và surcharges (giờ đêm, bốc xếp).<br>- Tạo payload VietQR chuẩn Napas247 chứa mã đơn và số tiền.<br>- Viết API Endpoint Webhook nhận callback xác nhận thanh toán thành công từ ngân hàng/cổng trung gian để tự động cập nhật đơn hàng thành `paid`. | - File: `/backend/app/api/v1/payments.py`<br>- DB Model: `Payment` | - Sinh đúng chuỗi VietQR String và ảnh QR dạng base64.<br>- Xử lý Webhook an toàn (idempotent request) tránh cộng tiền trùng lặp. |
| **Dev B (Frontend)** | - Code màn hình Checkout hiển thị chi tiết hoá đơn và ảnh VietQR.<br>- Lắng nghe qua WebSocket trạng thái thanh toán (hoặc poll API mỗi 5 giây) để tự động hiển thị màn hình "Thành công" khi backend nhận được tiền. | - Thư mục: `/frontend/lib/features/booking/presentation/pages/`<br>- UI: `PaymentPage` | - Màn hình tự chuyển sang trạng thái "Thanh toán thành công" khi Dev A trigger giả lập webhook nhận tiền. |

---

## 4. QUY TRÌNH HỢP NHẤT VÀ TÍCH HỢP LIÊN TỤC (INTEGRATION PROTOCOL)
Để đảm bảo hai dev khi gộp code (merge) không tạo ra lỗi dây chuyền:

1. **Local Test Giai Đoạn:**
   * Dev A chạy `pytest` trong `/backend`. Code backend phải pass 100% tests mới được tạo Pull Request vào `dev`.
   * Dev B chạy `flutter analyze` và `flutter test` trong `/frontend`. Flutter code không được có error/warning linter nào mới được tạo Pull Request.
2. **Merge Guardrail (CI):**
   * GitHub Actions sẽ chặn nút Merge trên PR nếu một trong hai pipeline CI (`Backend CI` hoặc `Frontend CI`) bị báo đỏ.
3. **Môi trường Stagging chung (VPS Dev):**
   * Dev A cấu hình tự động deploy code nhánh `dev` lên VPS staging sau khi PR được merge.
   * Dev B sẽ thay đổi cấu hình API URL trong Flutter từ `localhost` sang IP/Domain của staging server để test tích hợp cuối cùng.
