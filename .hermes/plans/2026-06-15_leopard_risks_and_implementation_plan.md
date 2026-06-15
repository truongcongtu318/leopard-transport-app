# KẾ HOẠCH TRIỂN KHAI, ĐÁNH GIÁ ĐỘ KHÓ & RỦI RO DỰ ÁN LEOPARD

**Tên dự án:** LEOPARD (Kết nối vận tải hàng hóa trọng tải lớn / xe tải / xe ba gác)
**Mục tiêu:** Xây dựng phiên bản Demo hoàn chỉnh, chạy ổn định trên môi trường Production.
**Ngân sách tối đa:** 15.000.000 VND (cứng, không phát sinh).
**Hạn bàn giao (Deadline):** Trước ngày 15/09/2026.

---

## 1. PHÂN TÍCH RỦI RO LỚN CỦA DỰ ÁN (PROJECT RISKS)

### Rủi ro 1: Ngân sách quá thấp (15,000,000 VND) so với yêu cầu tính năng
* **Mô tả:** Dự án yêu cầu rất nhiều công nghệ phức tạp: AI dự báo ETA (XGBoost), Tối ưu tuyến đường (OR-Tools VRP), Bản đồ dẫn đường chuyên dụng cho xe tải (tránh cấm tải, cầu thấp), Real-time Tracking. Chi phí riêng cho API (Google Maps, Vietmap) và Server chứa mô hình AI có thể nhanh chóng vượt qua ngân sách này nếu không được thiết kế tối giản.
* **Tác động:** Rất cao. Có thể cạn kiệt ngân sách trước khi có sản phẩm chạy được (Live Product).
* **Giải pháp giảm thiểu:** 
  * Sử dụng các giải pháp mã nguồn mở và miễn phí (OSRM - Open Source Routing Machine thay cho Vietmap/Google API trong giai đoạn demo).
  * Host server AI (nếu có) trên các cloud miễn phí hoặc dùng gói rẻ nhất (Hugging Face Spaces, Render, Koyeb hoặc tận dụng máy cá nhân làm server test).
  * Giới hạn phạm vi dữ liệu thử nghiệm trong 1 khu vực nhỏ (ví dụ: Quận 1, Quận Bình Thạnh tại TP.HCM) để tránh bùng nổ chi phí API bản đồ.

### Rủi ro 2: Thời gian triển khai ngắn (gần 3 tháng) đối với một hệ thống phức tạp
* **Mô tả:** Deadline là trước 15/09/2026. Hệ thống có 2 phân hệ (App Khách hàng & App Tài xế) kèm theo Backend quản trị và module tính toán AI/OR-Tools. Việc code từ đầu tất cả sẽ không kịp tiến độ.
* **Tác động:** Cao. Trễ deadline bàn giao.
* **Giải pháp giảm thiểu:**
  * Sử dụng Flutter để xây dựng ứng dụng đa nền tảng (1 codebase chạy cả Android & iOS/Web) để tiết kiệm thời gian code UI.
  * Tận dụng Firebase làm Backend-as-a-Service (FCM cho thông báo, Firebase Auth cho đăng nhập/OTP, Firestore cho real-time tracking và chat). Điều này giúp giảm 70% thời gian viết Backend.
  * Tránh "tự phát minh lại bánh xe": sử dụng thư viện OR-Tools có sẵn trên Python backend hoặc giải thuật tối ưu đơn giản hóa ở phía server.

### Rủi ro 3: Chi phí và độ chính xác của API Bản đồ (Vietmap vs Google Maps)
* **Mô tả:** Bản đồ cho xe tải (Truck-friendly navigation) cần biết tải trọng xe để tránh đường cấm, cầu yếu. Google Maps API không hỗ trợ dẫn đường tránh tải trọng ở Việt Nam một cách chính xác. Vietmap API hỗ trợ tốt hơn nhưng chi phí cực kỳ đắt và thủ tục đăng ký pháp lý phức tạp cho cá nhân/dự án nhỏ.
* **Tác động:** Trung bình đến Cao. Bản đồ chỉ đường sai làm tài xế bị phạt hoặc làm hỏng trải nghiệm người dùng.
* **Giải pháp giảm thiểu:**
  * **Giải pháp Demo:** Trên App chỉ vẽ đường dẫn cơ bản (Google Maps SDK miễn phí/giá rẻ cho hiển thị), còn phần cảnh báo cấm tải/cấm giờ sẽ là một lớp dữ liệu tĩnh (Static overlay) được cấu hình thủ công cho một vài tuyến đường mẫu tại khu vực thử nghiệm.
  * Tích hợp cơ chế cho tài xế tự báo cáo (Crowdsourcing) đường cấm để cập nhật hệ thống.

---

## 2. PHÂN TÍCH ĐỘ KHÓ KỸ THUẬT (TECHNICAL COMPLEXITY)

### Độ khó 1: AI dự báo ETA chính xác (XGBoost + Traffic real-time + Weather)
* **Thách thức:** Mô hình XGBoost cần dữ liệu lịch sử di chuyển lớn để huấn luyện (Data-hungry). Trong giai đoạn demo, chúng ta **không có sẵn tập dữ liệu này** ở Việt Nam. Việc lấy dữ liệu thời tiết (Weather API) và Traffic real-time để đưa vào mô hình đòi hỏi các API mất phí và xử lý dữ liệu phức tạp theo thời gian thực.
* **Giải pháp kỹ thuật:**
  * **Thiết kế tối giản (Scope-down):** Tạo một mô hình XGBoost đơn giản chạy trên Flask/FastAPI backend. Mô hình này nhận đầu vào là: Khoảng cách (từ OSRM), Thời gian trong ngày (Giờ cao điểm/Thấp điểm), và Thời tiết (Mưa/Nắng - lấy từ OpenWeatherMap API miễn phí).
  * **Huấn luyện giả lập:** Sử dụng dữ liệu giả lập (Synthesized data) dựa trên các chuyến đi thực tế tự tạo để train mô hình ban đầu nhằm chứng minh tính khả thi kỹ thuật (Proof of Concept - PoC).

### Độ khó 2: Tối ưu ghép hàng và tuyến đường (OR-Tools VRP)
* **Thách thức:** Vehicle Routing Problem (VRP) là một bài toán NP-hard. OR-Tools của Google rất mạnh nhưng đòi hỏi tài nguyên tính toán lớn và khó tích hợp trực tiếp trên thiết bị di động.
* **Giải pháp kỹ thuật:**
  * Đẩy phần tính toán này về Backend (Python FastAPI).
  * Khi khách hàng đặt đơn ghép, Backend sẽ chạy thuật toán OR-Tools trong một khoảng thời gian giới hạn (Time limit = 5-10 giây) để tìm ra phương án tối ưu tương đối thay vì tối ưu tuyệt đối, tránh làm treo server.

### Độ khó 3: Theo dõi thời gian thực (Real-time Tracking) & Tiết kiệm Pin
* **Thách thức:** App Tài xế cần cập nhật tọa độ GPS liên tục lên server để App Khách hàng theo dõi. Việc cập nhật GPS liên tục trên Flutter khi app chạy ngầm (Background mode) rất dễ bị hệ điều hành (Android/iOS) kill và gây tốn pin cực kỳ nhanh.
* **Giải pháp kỹ thuật:**
  * Sử dụng thư viện Flutter `flutter_background_service` hoặc `geolocator` cấu hình chạy ngầm với tần suất gửi tọa độ hợp lý (ví dụ: 10 giây/lần hoặc chỉ khi tài xế di chuyển quá 20 mét).
  * Sử dụng Firebase Firestore để đồng bộ vị trí theo thời gian thực (Firestore có cơ chế sync rất nhẹ và tự động).

---

## 3. ĐỀ XUẤT STACK CÔNG NGHỆ TỐI ƯU CHI PHÍ ($0 CHO DEMO)

Để đảm bảo ngân sách 15.000.000 VND không bị vượt trội:

* **Mobile App Client:** Flutter (Dart). Viết 1 source code duy nhất, phân quyền User bằng Role (Khách hàng / Tài xế).
* **Backend chính:** Firebase (Firestore làm DB real-time, Auth, Storage để lưu ảnh giấy tờ xe/hàng hóa, Cloud Functions nếu cần). Hạn mức miễn phí của Firebase hoàn toàn thừa sức gánh giai đoạn Demo.
* **Server thuật toán AI & OR-Tools:** Viết bằng Python (FastAPI). Deploy miễn phí hoặc chi phí siêu rẻ ($5/tháng) trên Render hoặc Koyeb.
* **Bản đồ hiển thị & Geocoding:** 
  * Map hiển thị: Google Maps Flutter SDK (dùng key miễn phí có hạn mức $200/tháng của Google).
  * Định tuyến (Routing): Dùng server OSRM miễn phí của cộng đồng hoặc tự dựng một instance OSRM siêu nhẹ trên VPS giá rẻ.
  * QR Thanh toán: VietQR API (miễn phí từ Napas) sinh mã QR động dựa trên số tài khoản ngân hàng và số tiền của đơn hàng.

---

## 4. LỘ TRÌNH TRIỂN KHAI CHI TIẾT (IMPLEMENTATION ROADMAP)

Lộ trình được chia làm 4 Phase từ nay đến 15/09/2026:

### Phase 1: Setup & Thiết kế Cơ sở Dữ liệu (15/06 - 30/06)
* **Mục tiêu:** Thiết lập cấu trúc dự án Flutter, cấu hình Firebase và thiết kế lược đồ dữ liệu (Schema) trên Firestore.
* **Các Task chi tiết:**
  * **Task 1.1:** Setup project Flutter mới, cấu hình Git repo sạch.
  * **Task 1.2:** Liên kết dự án với Firebase (Auth & Firestore).
  * **Task 1.3:** Thiết kế Firestore Schema gồm các collection: `users` (hồ sơ, giấy tờ), `orders` (trạng thái, vị trí lấy/giao, thông tin hàng, giá tiền, tài xế nhận), `tracking` (tọa độ GPS real-time của xe).

### Phase 2: Phát triển Tính năng Đăng nhập & Hồ sơ (01/07 - 15/07)
* **Mục tiêu:** Hoàn thành luồng Authentication và cập nhật hồ sơ đính kèm tài liệu pháp lý (GPLX, đăng ký xe).
* **Các Task chi tiết:**
  * **Task 2.1:** Đăng ký/Đăng nhập bằng Số điện thoại (Firebase Auth OTP) hoặc Google.
  * **Task 2.2:** Giao diện cập nhật hồ sơ cá nhân cho Khách hàng & Tài xế.
  * **Task 2.3:** Tính năng upload ảnh giấy tờ xe (cà vẹt, GPLX) lên Firebase Storage để duyệt thủ công trên console (không cần viết trang Admin duyệt để tiết kiệm thời gian).

### Phase 3: Tính năng Cốt lõi - Đặt đơn, Tracking & Thanh toán VietQR (16/07 - 15/08)
* **Mục tiêu:** Người dùng đặt được đơn, tài xế nhận đơn, xem bản đồ dẫn đường và theo dõi vị trí real-time, thanh toán qua QR.
* **Các Task chi tiết:**
  * **Task 3.1:** Giao diện đặt đơn (chọn đa điểm trên map Google, nhập cân nặng/kích thước hàng, chọn dịch vụ bốc xếp).
  * **Task 3.2:** Hệ thống phân phối đơn hàng (Tài xế xung quanh nhận được thông báo qua FCM và có thể bấm "Nhận đơn").
  * **Task 3.3:** Viết background service trên Flutter để cập nhật GPS tài xế lên Firestore khi di chuyển.
  * **Task 3.4:** Tích hợp VietQR tạo mã QR thanh toán động hiển thị cuối chuyến đi dựa trên thông tin số tài khoản của tài xế/chủ app.

### Phase 4: Tích hợp AI (ETA) & Tối ưu tuyến đường (OR-Tools) (16/08 - 31/08)
* **Mục tiêu:** Kết nối Backend Python để ước lượng thời gian đi chính xác và tối ưu gom hàng.
* **Các Task chi tiết:**
  * **Task 4.1:** Viết Backend Python (FastAPI) tích hợp thư viện OR-Tools để giải bài toán VRP gom đơn khi có nhiều đơn cùng tuyến.
  * **Task 4.2:** Viết module XGBoost dự đoán ETA dựa trên khoảng cách (OSRM API), thời tiết (OpenWeatherMap) và giờ cao điểm.
  * **Task 4.3:** Kết nối Flutter App gọi API từ FastAPI Backend này khi tạo đơn và khi tài xế di chuyển.

### Phase 5: Testing, Fix bug & Triển khai Production (01/09 - 15/09)
* **Mục tiêu:** Test chạy thực tế trên đường phố, tối ưu hiệu năng và bàn giao mã nguồn + tài liệu.
* **Các Task chi tiết:**
  * **Task 5.1:** Thực hiện test thực địa (chạy xe máy/xe tải mô phỏng ngoài đường để test độ trễ của GPS tracking).
  * **Task 5.2:** Tối ưu hóa UI/UX mượt mà, hạn chế tối đa việc gọi API bản đồ quá hạn mức miễn phí.
  * **Task 5.3:** Viết tài liệu hướng dẫn deploy chi tiết (Deploy FastAPI lên Render, cấu hình Firebase). Bàn giao source code sạch lên GitHub.

---

## 5. CÁC CÂU HỎI MỞ CẦN XÁC NHẬN VỚI NGƯỜI DÙNG (OPEN QUESTIONS)

1. **Về việc xác thực tài xế:** Trong bản demo, chúng ta có cần tích hợp OCR để tự động quét giấy tờ xe (GPLX/Cà vẹt) không, hay chỉ cần chụp ảnh upload lên rồi admin duyệt thủ công qua Firebase Console để tiết kiệm ngân sách?
2. **Về luồng thanh toán:** Có cần tự động đối soát giao dịch ngân hàng khi khách quét mã VietQR không (cần đăng ký dịch vụ bên thứ 3 mất phí), hay chỉ hiển thị ảnh mã QR để khách chuyển khoản thủ công và tài xế bấm xác nhận đã nhận tiền?
3. **Về phạm vi Demo:** Chúng ta sẽ khoanh vùng chạy thử nghiệm ở thành phố nào (ví dụ: TP.HCM hay Hà Nội) để chuẩn bị bộ dữ liệu giả lập cho AI ETA và OR-Tools tốt nhất?
