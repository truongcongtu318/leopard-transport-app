# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)
## DỰ ÁN: LEOPARD - HỆ THỐNG KẾT NỐI VẬN TẢI HÀNG HÓA TRỌNG TẢI LỚN

| Field | Value |
|---|---|
| **Tên tài liệu** | Software Requirements Specification (SRS) |
| **Dự án** | LEOPARD APP |
| **Phiên bản** | 1.0 |
| **Ngày tạo** | 2026-06-15 |
| **Trạng thái** | Draft / Review |
| **Tác giả** | PM & Tech Lead Team LEOPARD |
| **Đối tượng** | Đội ngũ Phát triển, Hội đồng Chấm Đồ án tốt nghiệp |

---

## 1. GIỚI THIỆU (INTRODUCTION)

### 1.1. Mục đích (Purpose)
Tài liệu SRS này đặc tả chi tiết toàn bộ các yêu cầu chức năng (Functional Requirements) và yêu cầu phi chức năng (Non-functional Requirements) cho ứng dụng kết nối vận tải hàng hóa LEOPARD. Tài liệu này đóng vai trò là "nguồn sự thật duy nhất" (Single Source of Truth) phục vụ cho:
- Đội ngũ lập trình phát triển frontend (Flutter) và backend (FastAPI).
- Đội ngũ kiểm thử viết Test Case và Test Plan.
- Hội đồng đánh giá đồ án tốt nghiệp kiểm tra mức độ hoàn thành và tính đúng đắn của sản phẩm so với plan ban đầu.

### 1.2. Phạm vi sản phẩm (Product Scope)
LEOPARD là nền tảng kết nối trực tiếp chủ hàng (SME, cá nhân chuyển nhà, nhà máy nông sản) với tài xế xe tải/xe ba gác freelance hoặc đội xe nhỏ. 
- **Hệ thống bao gồm:**
  1. **Mobile App (Flutter):** Dành cho Khách hàng (đặt đơn, theo dõi) và Tài xế (nhận đơn, định tuyến dẫn đường).
  2. **Web Portal (Flutter Web/HTML):** Dashboard quản lý cho các Doanh nghiệp SME (quản lý đội xe, đối soát thanh toán).
  3. **Backend API Server (FastAPI):** Xử lý nghiệp vụ logic, WebSocket kết nối real-time.
  4. **AI & Optimization Engine (Python):** XGBoost dự báo ETA và Google OR-Tools tối ưu hóa tuyến đường ghép hàng VRP.
  5. **Bản đồ số (Vietmap Integration):** Dẫn đường tránh cấm tải, cấm giờ, autocomplete địa chỉ.

### 1.3. Định nghĩa & Thuật ngữ (Definitions & Acronyms)
| Thuật ngữ | Định nghĩa |
|---|---|
| **SME** | Small and Medium Enterprise (Doanh nghiệp vừa và nhỏ) |
| **ETA** | Estimated Time of Arrival (Thời gian dự kiến đến nơi) |
| **ETD** | Estimated Time of Departure (Thời gian dự kiến xuất phát) |
| **VRP** | Vehicle Routing Problem (Bài toán định tuyến phương tiện) |
| **VietQR** | Chuẩn mã QR thanh toán nhanh bằng ngân hàng tại Việt Nam (NAPAS) |
| **FCM** | Firebase Cloud Messaging (Dịch vụ gửi thông báo đẩy) |
| **GPLX / Cà-vẹt** | Giấy phép lái xe / Giấy đăng ký xe |
| **COD** | Cash on Delivery (Thanh toán tiền mặt khi giao hàng) |
| **OSRM** | Open Source Routing Machine (Engine định tuyến mã nguồn mở) |
| **AC** | Acceptance Criteria (Tiêu chí nghiệm thu) |

---

## 2. MÔ TẢ TỔNG QUAN (OVERALL DESCRIPTION)

### 2.1. Bối cảnh sản phẩm (Product Perspective)
LEOPARD ra đời nhằm giải quyết sự thiếu hụt các ứng dụng vận tải chuyên sâu cho phân khúc xe tải vừa và lớn tại Việt Nam. Các ứng dụng hiện tại (như Lalamove, GrabExpress) chủ yếu tập trung vào xe máy hoặc xe tải nhỏ (< 2 tấn) và định tuyến thông thường không tránh được các ràng buộc phức tạp của xe tải lớn (đường cấm tải, cầu thấp, giờ cấm xe vào nội thành). LEOPARD tập trung giải quyết bài toán định vị không gian phức tạp và tối ưu hóa chi phí vận hành bằng AI.

### 2.2. Các tác nhân trong hệ thống (User Classes and Characteristics)
Hệ thống LEOPARD phục vụ 4 nhóm đối tượng chính:

```
                  ┌──────────────────────────────┐
                  │       LEOPARD SYSTEM         │
                  └──────────────┬───────────────┘
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ 1. Khách hàng    │   │ 2. Tài xế        │   │ 3. Doanh nghiệp │
│ (Shipper)        │   │ (Driver)         │   │ (Fleet Owner)    │
│ - Đặt đơn        │   │ - Nhận đơn       │   │ - Quản lý xe     │
│ - Trả tiền       │   │ - Chạy xe        │   │ - Đối soát       │
│ - Theo dõi đơn   │   │ - Upload giấy tờ │   │ - Tạo hợp đồng   │
└──────────────────┘   └──────────────────┘   └──────────────────┘
                                 │
                                 ▼
                       ┌──────────────────┐
                       │ 4. Admin         │
                       │ - Duyệt tài xế   │
                       │ - Quản lý hệ thống│
                       └──────────────────┘
```

1. **Khách hàng cá nhân / Shipper SME:**
   - Cần đặt xe nhanh, biết trước giá chính xác và thời gian giao hàng (ETA).
   - Yêu cầu giao diện tối giản, hiển thị bản đồ trực quan.
2. **Tài xế tự do (Freelance Driver):**
   - Sử dụng app điện thoại để nhận cuốc xe, xem lộ trình dẫn đường.
   - Cần tính năng dẫn đường "truck-friendly" tránh cấm đường để không bị phạt giao thông.
3. **Doanh nghiệp vận tải / Fleet Owner:**
   - Quản lý danh sách nhiều tài xế và đầu xe (Fleet).
   - Xem dashboard báo cáo hiệu suất xe, doanh thu, thanh toán định kỳ.
4. **Quản trị viên (Admin):**
   - Kiểm tra, duyệt hồ sơ giấy tờ của tài xế (GPLX, đăng kiểm xe) trước khi cho phép hoạt động.

### 2.3. Ràng buộc thiết kế & Triển khai (Constraints)
1. **Ràng buộc phần cứng/hạ tầng:** Hệ thống được thiết kế để triển khai trên 1 VPS Linux duy nhất (RAM tối thiểu 2GB, CPU 2 Cores) để tiết kiệm chi phí trong giai đoạn đầu.
2. **Ràng buộc pháp lý:** Hệ thống phải lưu trữ hồ sơ tài xế và phương tiện theo đúng quy định pháp luật Việt Nam về kinh doanh vận tải đường bộ.
3. **Ràng buộc API:** Tần suất gọi API Vietmap không vượt quá giới hạn free tier (500 request/ngày cho Routing/Autocomplete).

---

## 3. TÍNH NĂNG CHI TIẾT (SYSTEM FEATURES & USER STORIES)

### 3.1. Phân hệ Đăng ký, Đăng nhập & Xác thực (Auth & Profile)

#### User Story 1.1: Đăng nhập OTP qua Số Điện Thoại
- **Là** một tài xế hoặc khách hàng mới,
- **Tôi muốn** đăng ký/đăng nhập nhanh bằng số điện thoại nhận mã OTP qua SMS,
- **Để** tôi có thể truy cập app lập tức mà không cần nhớ mật khẩu phức tạp.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Hỗ trợ đầu số điện thoại Việt Nam (+84 hoặc 0).
  2. Firebase Auth gửi OTP SMS thành công trong vòng < 15 giây.
  3. Cho phép nhập mã OTP gồm 6 chữ số. Có cơ chế cooldown 60 giây trước khi yêu cầu gửi lại OTP.
  4. Nếu số điện thoại chưa tồn tại trong DB, chuyển hướng sang màn hình cập nhật Profile cơ bản (Họ tên, Vai trò).

#### User Story 1.1b: Đăng nhập nhanh bằng tài khoản Google (OAuth)
- **Là** một khách hàng cá nhân hoặc doanh nghiệp (Shipper),
- **Tôi muốn** đăng nhập nhanh vào ứng dụng bằng tài khoản Google sẵn có của mình trên điện thoại/web,
- **Để** tôi không phải nhập số điện thoại hoặc mã OTP thủ công.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Tích hợp nút "Đăng nhập bằng Google" (Google Sign-In) trên màn hình Auth.
  2. Tích hợp Firebase Auth Google Provider trên cả Flutter Mobile và Flutter Web.
  3. Thời gian hoàn thành flow authentication (từ khi chọn tài khoản Google đến khi chuyển hướng vào màn hình chính) < 3 giây.
  4. Tự động trích xuất: Họ tên, Email, Avatar URL từ tài khoản Google để điền vào profile của user trong DB.
  5. Đối với tài xế, bắt buộc phải dùng Số điện thoại (OTP SMS) để định danh chính xác, không dùng Google Sign-In độc lập. Nếu đăng ký vai trò Driver từ Google Auth, hệ thống sẽ yêu cầu verify số điện thoại ở bước tiếp theo.

#### User Story 1.2: Cung cấp giấy tờ pháp lý của tài xế
- **Là** một tài xế xe tải lớn đăng ký hoạt động trên app,
- **Tôi muốn** chụp ảnh và upload các giấy tờ bắt buộc gồm: Giấy phép lái xe (GPLX), Cà-vẹt xe, Giấy đăng kiểm xe và bảo hiểm dân sự,
- **Để** admin hệ thống phê duyệt tài khoản và xe của tôi được hoạt động hợp pháp.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Giao diện cho phép chọn loại giấy tờ và chụp ảnh trực tiếp bằng camera hoặc chọn từ gallery.
  2. Định dạng ảnh hỗ trợ: JPG, PNG. Dung lượng tối đa 5MB/ảnh.
  3. Giấy tờ upload xong được lưu ở trạng thái `Pending Approval` (Chờ duyệt).
  4. Tài xế không thể nhận đơn nếu chưa có tối thiểu 1 xe ở trạng thái `Approved` (Đã duyệt).

---

### 3.2. Phân hệ Đặt đơn hàng đa điểm (Multi-stop Booking Flow)

#### User Story 2.1: Tạo đơn hàng giao đa điểm
- **Là** một chủ cửa hàng vật liệu xây dựng (SME),
- **Tôi muốn** nhập điểm lấy hàng và tối đa 5 điểm giao hàng trung gian, chụp ảnh hàng hóa và nhập tải trọng hàng,
- **Để** tôi có thể vận chuyển hàng hóa cho nhiều công trình cùng một lúc trong một chuyến xe.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Bản đồ hiển thị rõ thứ tự các điểm dừng: Pickup (A) -> Stop 1 (B) -> Stop 2 (C)... -> Destination (D).
  2. Input địa chỉ hỗ trợ **Vietmap Autocomplete API** gợi ý địa chỉ tiếng Việt khi gõ từ 3 ký tự.
  3. Cho phép người dùng nhập các thuộc tính bắt buộc của hàng hóa:
     - Tổng trọng lượng (kg / tấn).
     - Kích thước (Dài x Rộng x Cao).
     - Có yêu cầu bốc xếp (Có/Không).
     - Số điện thoại người nhận tại mỗi điểm giao.
  4. Hệ thống gọi API định giá động (Dynamic Pricing Engine) dựa trên khoảng cách đi và tải trọng xe yêu cầu để hiển thị giá tiền ngay lập tức trước khi xác nhận đặt đơn.

```
Luồng đặt đơn hàng (Booking Flow):
[Nhập địa chỉ A -> B -> C] ──> [Vietmap API Autocomplete] ──> [Chọn loại xe tải phù hợp]
          │
          ▼
[Xác nhận bốc xếp, chụp ảnh hàng] ──> [FastAPI tính tiền] ──> [Hiển thị VietQR thanh toán]
```

---

### 3.3. Phân hệ Bản đồ & Định tuyến Truck-Friendly (GIS & Routing)

#### User Story 3.1: Dẫn đường tránh cấm tải và cấm giờ
- **Là** một tài xế xe tải lớn 15 tấn,
- **Tôi muốn** hệ thống hiển thị bản đồ dẫn đường đi tránh các tuyến đường cấm xe > 10 tấn, tránh cầu có chiều cao giới hạn dưới 4m và tránh giờ cao điểm cấm xe tải đi vào nội đô,
- **Để** tôi di chuyển an toàn, nhanh chóng và không vi phạm luật giao thông đường bộ.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Khi tài xế ấn "Bắt đầu chuyến đi" (Start Trip), app gửi thuộc tính xe (Chiều cao, Tải trọng, Giờ hiện tại) sang backend.
  2. Backend gọi **Vietmap Routing API với Truck Profile** (hoặc Local OSRM Engine có cấu hình `truck.lua` nếu Vietmap quá tải).
  3. Lộ trình vẽ trên app Flutter Map của tài xế phải là đường đi khả thi không đi qua các nút cấm tải/cấm chiều cao theo thông số xe.
  4. Nếu tài xế đi chệch hướng quá 100m, hệ thống tự động tính toán lại route mới (Recalculate Route) trong < 3 giây.

---

### 3.4. Phân hệ Real-time Tracking (WebSocket & GPS)

#### User Story 4.1: Theo dõi xe di chuyển trực tiếp trên bản đồ
- **Là** một shipper đang chờ hàng đến,
- **Tôi muốn** nhìn thấy vị trí thực tế của xe tải di chuyển trên bản đồ theo thời gian thực và thời gian dự kiến giao hàng (ETA) đếm ngược,
- **Để** tôi chủ động sắp xếp nhân công và kho bãi chuẩn bị dỡ hàng.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Khi tài xế di chuyển, SDK điện thoại lấy GPS coordinate gửi lên backend qua kết nối **WebSocket** mỗi 5 giây/lần.
  2. Backend phát (Pub/Sub qua Redis) vị trí đó đến client của shipper tương ứng đang mở màn hình tracking.
  3. Marker biểu tượng xe tải trên bản đồ shipper di chuyển mượt mà (sử dụng Lerp interpolation ở client để tránh giật lag xe).
  4. Đồng hồ đếm ngược ETA cập nhật liên tục dựa trên khoảng cách thực tế còn lại.

---

### 3.5. Phân hệ AI Dự báo ETA chính xác (XGBoost ETA)

#### User Story 5.1: Dự báo thời gian giao hàng chính xác dựa trên thời tiết và giao thông
- **Là** một doanh nghiệp nông sản cần vận chuyển rau quả tươi vào thành phố,
- **Tôi muốn** hệ thống hiển thị thời gian giao hàng dự báo chính xác (sai số thấp),
- **Để** đảm bảo hàng hóa nông sản không bị hỏng do chờ đợi quá lâu mà không có kế hoạch.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Mô hình XGBoost dự báo ETA được host trên API backend nhận input đầu vào:
     - Quãng đường định tuyến (km).
     - Thời tiết hiện tại (Lấy từ OpenWeather API theo toạ độ: Mưa/Nắng/Mây).
     - Giờ xuất phát (Hour of day, Day of week).
     - Tình trạng kẹt xe (Traffic density từ Vietmap).
  2. Kết quả trả về gồm: ETA dự kiến (phút) và khoảng tin cậy 90% (ví dụ: "40 - 50 phút").
  3. Độ chính xác của model đạt sai số trung bình tuyệt đối **MAE < 5 phút** trên tập dữ liệu kiểm thử (Validation set).

---

### 3.6. Phân hệ Tối ưu ghép hàng và tuyến đường (OR-Tools VRP)

#### User Story 6.1: Gợi ý đơn ghép dọc đường về
- **Là** một tài xế xe tải tự do vừa hoàn thành cuốc giao hàng ở Bình Dương về TP.HCM,
- **Tôi muốn** hệ thống tự động gợi ý 1-2 đơn hàng nhỏ lẻ đang chờ chuyển từ Bình Dương về TP.HCM nằm trên trục đường di chuyển của tôi,
- **Để** tôi tăng doanh thu chuyến về, tối ưu hóa tiền xăng và giảm thiểu quãng đường chạy xe rỗng.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Backend kích hoạt giải thuật **Google OR-Tools VRP** chạy ngầm (Celery worker) khi tài xế nhấn "Hoàn thành" đơn hàng hiện tại.
  2. Thuật toán tìm kiếm các đơn hàng ở trạng thái `Pending` trong bán kính 10km xung quanh điểm trả hàng hiện tại của tài xế.
  3. Ràng buộc giải thuật:
     - Sức chứa xe còn trống ≥ Trọng lượng đơn ghép.
     - Thời gian giao đơn ghép không làm trễ khung giờ yêu cầu (Time Windows).
     - Quãng đường chệch hướng tối đa của tài xế (detour distance) không vượt quá 5km.
  4. Nếu tìm thấy phương án tối ưu, hệ thống gửi thông báo đẩy (FCM) tới tài xế với nút "Nhận ghép đơn" kèm thông tin giá cước cộng thêm. Tài xế có 30 giây để chấp nhận trước khi đơn chuyển cho tài xế khác.

---

### 3.7. Phân hệ Tích hợp thanh toán QR Ngân hàng (VietQR)

#### User Story 7.1: Thanh toán quét mã VietQR động
- **Là** một khách hàng đặt cuốc xe,
- **Tôi muốn** màn hình hiển thị một mã QR thanh toán ngân hàng (VietQR) có kèm sẵn số tiền và nội dung chuyển khoản chính xác của đơn hàng,
- **Để** tôi có thể quét nhanh bằng ứng dụng Mobile Banking của bất kỳ ngân hàng nào mà không cần nhập thủ công số tài khoản và số tiền dễ bị sai sót.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Mã QR được sinh động dựa trên chuẩn mã hóa của NAPAS (VietQR specs).
  2. Nội dung mã QR bao gồm: Mã ngân hàng nhận (BIN), Số tài khoản nhận, Số tiền chính xác của đơn hàng, và Nội dung chuyển khoản duy nhất chứa ID đơn hàng (Ví dụ: `LEOPARD ORD12345`).
  3. Có màn hình hướng dẫn người dùng quét mã. Giai đoạn này chỉ cần hiển thị QR, chưa cần webhook tự động nhận tiền từ ngân hàng (người dùng nhấn "Xác nhận đã chuyển khoản" để hoàn thành, tài xế xác nhận đã nhận tiền).

---

---

### 3.8. Phân hệ Thông báo & Tin nhắn (Notifications & Chat)

#### User Story 8.1: Nhận thông báo đẩy khi trạng thái đơn hàng thay đổi
- **Là** một shipper đã đặt hàng hoặc một tài xế đã nhận đơn,
- **Tôi muốn** nhận thông báo đẩy (Push Notification) tức thời qua điện thoại khi có sự kiện quan trọng như: Có tài xế nhận đơn, Hàng đã đến nơi, Thanh toán thành công,
- **Để** tôi không cần phải mở app liên tục kiểm tra trạng thái.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Tích hợp Firebase Cloud Messaging (FCM) cho cả Flutter (Android, iOS) và Flutter Web.
  2. Danh sách sự kiện gửi thông báo: `order_assigned`, `driver_arrived`, `order_picked_up`, `order_delivered`, `payment_received`, `document_approved`, `document_rejected`, `document_expiring_soon`.
  3. Mỗi thông báo khi nhấn vào phải Deep Link đến màn hình chi tiết tương ứng trong app (ví dụ: click "Tài xế đã đến điểm lấy hàng" → mở màn hình tracking order).
  4. Lưu lịch sử thông báo trong bảng `notifications` của PostgreSQL để user có thể xem lại các thông báo đã nhận.
  5. Hỗ trợ tắt/bật thông báo theo từng loại sự kiện trong Settings.

#### User Story 8.2: Gửi tin nhắn nhanh giữa shipper và tài xế trong chuyến đi
- **Là** một tài xế đang vận chuyển hàng,
- **Tôi muốn** có thể gọi điện và nhắn tin nhanh trực tiếp với shipper trong app (không lộ số điện thoại cá nhân),
- **Để** tôi thông báo tình huống phát sinh (kẹt xe, tìm địa chỉ...) mà không làm lộ thông tin liên lạc cá nhân.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Tính năng **Gọi điện ẩn danh (Anonymous Call)** dùng Firebase Callable Functions hoặc SIP trunking để che giấu số điện thoại thực.
  2. Khi tài xế nhấn "Gọi", cuộc gọi được routing qua server, shipper thấy số ảo (không phải số thật của tài xế).
  3. Tính năng **Chat nhanh (In-app Chat)** lưu trữ trong PostgreSQL (bảng `messages`) hoặc dùng Firebase Realtime Database để real-time sync.
  4. Lịch sử chat được lưu và xoá sau 30 ngày kể từ khi đơn hàng kết thúc.
  5. Trong giai đoạn MVP, ưu tiên triển khai **In-app Chat với WebSocket + message persistence**. Tính năng gọi ẩn danh được ghi nhận là cần có phiên bản roadmap sau MVP.

---

### 3.9. Phân hệ Tìm kiếm & Bộ lọc Đơn hàng (Search & Filter)

#### User Story 9.1: Tìm kiếm đơn hàng và tài xế theo nhiều tiêu chí
- **Là** một tài xế muốn tìm đơn hàng phù hợp với xe của mình,
- **Tôi muốn** xem danh sách đơn hàng đang chờ và lọc theo các tiêu chí: loại xe yêu cầu, khoảng cách từ vị trí hiện tại, khoảng giá, điểm lấy hàng,
- **Để** tôi nhanh chóng chọn được đơn hàng phù hợp nhất với năng lực xe của mình.

- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Màn hình Tìm kiếm đơn hàng (Shipper Side: tìm tài xế / Driver Side: tìm đơn) hỗ trợ tối thiểu 3 bộ lọc:
     - **Loại xe:** Xe ba gác, Xe tải < 2 tấn, 2-5 tấn, 5-10 tấn, > 10 tấn.
     - **Khoảng cách:** < 5km, 5-10km, 10-20km, > 20km từ vị trí hiện tại (dùng PostGIS spatial query).
     - **Khoảng giá:** (Shipper đặt) hoặc (Tài xế đặt giá chào).
  2. Kết quả hiển thị dạng danh sách + bản đồ (map với markers các đơn/xe khả dụng).
  3. Thời gian load kết quả tìm kiếm đầu tiên < 2 giây trên mạng 4G.
  4. Cache kết quả tìm kiếm trên Redis với TTL 30 giây để tránh gọi DB liên tục.

---

## 4. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS)

### 4.1. Hiệu năng (Performance)
1. **Thời gian phản hồi API (Latency):** 95% số lượng request API CRUD thông thường phải được phản hồi dưới **200ms**.
2. **Thời gian tính toán định tuyến (Routing Speed):** API tìm đường đi của OSRM/Vietmap phải phản hồi dưới **100ms** cho chặng dưới 50km.
3. **Thời gian chạy giải thuật VRP (OR-Tools):** Giải thuật tối ưu hóa ghép đường cho tối đa 20 điểm giao hàng và 5 xe tải phải hoàn thành dưới **15 giây**.
4. **Khả năng chịu tải (Concurrency):** Hệ thống trên VPS cấu hình thấp phải chịu tải được ít nhất **100 kết nối WebSocket hoạt động đồng thời** gửi location GPS liên tục mà không gây tràn bộ nhớ (OOM).

### 4.2. Bảo mật (Security)
1. **Mã hóa đường truyền:** 100% dữ liệu truyền tải giữa Mobile/Web và Server phải được mã hóa qua giao thức HTTPS và WSS (Secure WebSockets).
2. **Xác thực API:** Các endpoint API nhạy cảm phải được bảo vệ bằng JWT token (JSON Web Token) có thời hạn hết hạn là 24 giờ.
3. **Phân quyền truy cập (Authorization):** Áp dụng Role-Based Access Control (RBAC). Tài xế không thể gọi API cập nhật đơn hàng của shipper khác, shipper không thể tự duyệt giấy tờ lái xe.
4. **Giới hạn tấn công (Rate Limiting):** Sử dụng Redis Token Bucket để giới hạn mỗi địa chỉ IP chỉ được gọi tối đa 60 requests/phút.

### 4.3. Tính an toàn & Tin cậy (Reliability & Safety)
1. **Lưu trữ vị trí lịch sử (Auditing):** Toạ độ GPS của tài xế trong suốt chuyến đi phải được lưu trữ an toàn trong PostgreSQL (TimescaleDB) để làm bằng chứng giải quyết tranh chấp khi xảy ra thất thoát hàng hóa.
2. **Tính toàn vẹn dữ liệu (ACID):** Khi xảy ra lỗi kết nối mạng trong quá trình đặt đơn, DB phải rollback trạng thái, không tạo ra đơn hàng rác (orphan records).
3. **Offline Caching:** App Mobile phải cache lại các thông tin cơ bản (thông tin tài xế, thông tin cuốc xe hiện tại) để khi mất sóng dọc đường (đèo dốc, tỉnh lộ), app vẫn hiển thị giao diện và ghi đè GPS coordinates vào local storage, sau khi có mạng lại sẽ sync lên server.

---

## 5. MA TRẬN PHÂN QUYỀN (MATRIX OF ACCESS RIGHTS)

| Chức năng / API | Guest | Shipper | Driver | Fleet Owner | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| Đăng ký / Đăng nhập | R/W | R | R | R | R |
| Đặt đơn hàng mới | - | R/W | - | R/W | R |
| Nhận đơn hàng | - | - | R/W | - | R |
| Xem lịch trình xe chạy (Real-time map) | - | R | R | R | R |
| Upload Giấy tờ xe / GPLX | - | - | R/W | R/W | R |
| Phê duyệt giấy tờ tài xế | - | - | - | - | R/W |
| Xem Dashboard Đội xe doanh nghiệp | - | - | - | R/W | R |
| Cấu hình hệ thống & rate limit | - | - | - | - | R/W |

*(Ghi chú: R = Read, W = Write, - = No Access)*

---

## 6. TIÊU CHÍ NGHIỆM THU TỔNG THỂ (OVERALL ACCEPTANCE CRITERIA)

Một tính năng được coi là hoàn thành (Definition of Done - DoD) khi đáp ứng:
1. **Code quality:** Không chứa warning nghiêm trọng từ linter (`dart analyze` cho Flutter, `flake8/mypy` cho Python).
2. **Testing coverage:** Viết tối thiểu unit test cho các service cốt lõi (FastAPI calculations, OR-Tools constraints, XGBoost input validation).
3. **Review:** Mọi Pull Request phải được review và merge thành công trên nhánh `main` của GitHub repository.
4. **Deployment:** Chạy ổn định trên môi trường staging/production Docker-compose mà không bị restart đột ngột.
