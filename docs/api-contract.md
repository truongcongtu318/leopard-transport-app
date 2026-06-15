# Tài liệu Hợp đồng API (API Contract) - Dự án LEOPARD

Dự án LEOPARD là ứng dụng kết nối xe tải chở hàng tại Việt Nam. Tài liệu này mô tả chi tiết các REST API Endpoints, WebSocket Events, Schemas và cấu trúc dữ liệu cho Backend (FastAPI) và Frontend (Flutter).

---

## 1. Thông tin chung (General Information)
- **Base URL (REST):** `https://api.leopard.vn/api/v1`
- **Base URL (WebSocket):** `wss://api.leopard.vn/ws/v1`
- **Content-Type:** `application/json`
- **Phương thức xác thực (Authentication):** Sử dụng Bearer Token (JWT) truyền qua Header `Authorization: Bearer <JWT_TOKEN>`

---

## 2. Xác thực (Authentication)

### 2.1. Yêu cầu gửi mã OTP qua Số điện thoại
Yêu cầu hệ thống gửi mã OTP xác thực qua SMS tới số điện thoại của người dùng (Tài xế hoặc Khách hàng).

- **Endpoint:** `POST /auth/phone/otp-request`
- **Xác thực:** Không yêu cầu (Public)
- **Request Body:**
```json
{
  "phone_number": "+84987654321",
  "role": "customer"
}
```
*Ghi chú: `role` có thể là `"customer"` hoặc `"driver"`.*

- **Response (200 OK):**
```json
{
  "success": true,
  "message": "Mã OTP đã được gửi thành công qua SMS.",
  "session_id": "otp_session_9a8b7c6d5e4f3g2h"
}
```
- **Response (400 Bad Request):**
```json
{
  "error_code": "INVALID_PHONE_NUMBER",
  "message": "Số điện thoại không đúng định dạng quốc tế (+84...)"
}
```

### 2.2. Xác thực OTP & Đăng nhập
Xác thực mã OTP được gửi đến điện thoại và trả về Access Token / Refresh Token.

- **Endpoint:** `POST /auth/phone/otp-verify`
- **Xác thực:** Không yêu cầu (Public)
- **Request Body:**
```json
{
  "phone_number": "+84987654321",
  "session_id": "otp_session_9a8b7c6d5e4f3g2h",
  "otp_code": "123456",
  "device_token": "fCM_token_example_1234567890"
}
```

- **Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdXN0XzAxIiwicm9sZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzE4NTg5MTk5fQ.signature",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdXN0XzAxIiwicm9sZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzIwMTg5MTk5fQ.signature",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "cust_01",
    "phone_number": "+84987654321",
    "full_name": "Nguyen Van A",
    "role": "customer",
    "is_active": true
  }
}
```
- **Response (401 Unauthorized):**
```json
{
  "error_code": "OTP_EXPIRED_OR_INVALID",
  "message": "Mã OTP không chính xác hoặc đã hết hạn."
}
```

### 2.3. Đăng nhập qua Google
Xác thực tài khoản bằng Google ID Token được lấy từ phía Flutter client.

- **Endpoint:** `POST /auth/google`
- **Xác thực:** Không yêu cầu (Public)
- **Request Body:**
```json
{
  "id_token": "ya29.a0AfB_byE8...google_id_token_content...",
  "role": "customer",
  "device_token": "fCM_token_example_1234567890"
}
```

- **Response (200 OK - Tài khoản đã tồn tại và liên kết):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdXN0XzAyIiwicm9sZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzE4NTg5MTk5fQ.signature",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdXN0XzAyIiwicm9sZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzIwMTg5MTk5fQ.signature",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "cust_02",
    "phone_number": null,
    "email": "customer.example@gmail.com",
    "full_name": "Tran Thi B",
    "role": "customer",
    "is_active": true
  }
}
```

---

## 3. Tối ưu hóa lộ trình & Đặt xe nhiều điểm (Multi-stop Booking & OR-Tools)

Hệ thống hỗ trợ đặt chuyến xe tải đi qua nhiều điểm dừng (Multi-stop). Để tối ưu chi phí và thời gian đi lại, người dùng có thể gửi yêu cầu tối ưu hóa lộ trình bằng Google OR-Tools trước khi tiến hành đặt xe chính thức.

### 3.1. Tối ưu hóa lộ trình (OR-Tools Route Optimization)
Nhận vào điểm xuất phát và danh sách các điểm giao/nhận hàng, trả về danh sách các điểm dừng đã được sắp xếp lại theo thứ tự tối ưu nhất dựa trên các ràng buộc về: khung giờ nhận hàng (Time Windows), tải trọng xe (Vehicle Capacity), và thời gian bốc xếp hàng (Service Time).

- **Endpoint:** `POST /bookings/optimize`
- **Xác thực:** Yêu cầu (Bearer Token)
- **Request Body:**
```json
{
  "vehicle_constraints": {
    "max_weight_kg": 2500,
    "max_volume_cbm": 12.5,
    "truck_type": "2.5_ton_covered"
  },
  "depot": {
    "address": "Cảng Cát Lái, Thạnh Mỹ Lợi, Quận 2, TP. Hồ Chí Minh",
    "latitude": 10.7635,
    "longitude": 106.7992,
    "earliest_departure": "2026-06-16T08:00:00Z"
  },
  "stops": [
    {
      "stop_id": "stop_01",
      "address": "12 Phan Chu Trinh, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
      "latitude": 10.7725,
      "longitude": 106.6980,
      "weight_kg": 500,
      "volume_cbm": 2.5,
      "service_time_minutes": 20,
      "time_window": {
        "start_time": "2026-06-16T08:30:00Z",
        "end_time": "2026-06-16T10:30:00Z"
      }
    },
    {
      "stop_id": "stop_02",
      "address": "456 Lê Văn Việt, Tăng Nhơn Phú A, Quận 9, TP. Hồ Chí Minh",
      "latitude": 10.8441,
      "longitude": 106.7825,
      "weight_kg": 1200,
      "volume_cbm": 6.0,
      "service_time_minutes": 35,
      "time_window": {
        "start_time": "2026-06-16T09:00:00Z",
        "end_time": "2026-06-16T12:00:00Z"
      }
    },
    {
      "stop_id": "stop_03",
      "address": "789 Nguyễn Văn Linh, Tân Phong, Quận 7, TP. Hồ Chí Minh",
      "latitude": 10.7294,
      "longitude": 106.7001,
      "weight_kg": 600,
      "volume_cbm": 3.0,
      "service_time_minutes": 15,
      "time_window": {
        "start_time": "2026-06-16T08:00:00Z",
        "end_time": "2026-06-16T17:00:00Z"
      }
    }
  ]
}
```

- **Response (200 OK):**
```json
{
  "optimization_status": "OPTIMAL",
  "total_distance_meters": 32500,
  "total_duration_minutes": 115,
  "optimized_route": [
    {
      "sequence": 0,
      "stop_id": "depot",
      "address": "Cảng Cát Lái, Thạnh Mỹ Lợi, Quận 2, TP. Hồ Chí Minh",
      "latitude": 10.7635,
      "longitude": 106.7992,
      "estimated_arrival": "2026-06-16T08:00:00Z",
      "estimated_departure": "2026-06-16T08:00:00Z"
    },
    {
      "sequence": 1,
      "stop_id": "stop_01",
      "address": "12 Phan Chu Trinh, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
      "latitude": 10.7725,
      "longitude": 106.6980,
      "estimated_arrival": "2026-06-16T08:25:00Z",
      "estimated_departure": "2026-06-16T08:45:00Z"
    },
    {
      "sequence": 2,
      "stop_id": "stop_03",
      "address": "789 Nguyễn Văn Linh, Tân Phong, Quận 7, TP. Hồ Chí Minh",
      "latitude": 10.7294,
      "longitude": 106.7001,
      "estimated_arrival": "2026-06-16T09:05:00Z",
      "estimated_departure": "2026-06-16T09:20:00Z"
    },
    {
      "sequence": 3,
      "stop_id": "stop_02",
      "address": "456 Lê Văn Việt, Tăng Nhơn Phú A, Quận 9, TP. Hồ Chí Minh",
      "latitude": 10.8441,
      "longitude": 106.7825,
      "estimated_arrival": "2026-06-16T09:55:00Z",
      "estimated_departure": "2026-06-16T10:30:00Z"
    }
  ]
}
```

### 3.2. Tạo đơn đặt xe (Create Booking)
Gửi yêu cầu khởi tạo một chuyến đi mới trên hệ thống dựa trên lộ trình đã được chọn hoặc tối ưu hóa.

- **Endpoint:** `POST /bookings/create`
- **Xác thực:** Yêu cầu (Bearer Token)
- **Request Body:**
```json
{
  "customer_id": "cust_01",
  "truck_type": "2.5_ton_covered",
  "cargo_type": "Hàng tiêu dùng nhanh (FMCG)",
  "total_weight_kg": 2300,
  "total_volume_cbm": 11.5,
  "payment_method": "VIETQR",
  "special_instructions": "Hàng dễ vỡ, yêu cầu ràng buộc kỹ và tài xế hỗ trợ nâng hạ đuôi xe.",
  "stops": [
    {
      "sequence": 0,
      "address": "Cảng Cát Lái, Thạnh Mỹ Lợi, Quận 2, TP. Hồ Chí Minh",
      "latitude": 10.7635,
      "longitude": 106.7992,
      "contact_name": "Nguyen Van A",
      "contact_phone": "+84987654321",
      "stop_type": "PICKUP"
    },
    {
      "sequence": 1,
      "address": "12 Phan Chu Trinh, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
      "latitude": 10.7725,
      "longitude": 106.6980,
      "contact_name": "Le Hoang B",
      "contact_phone": "+84912345678",
      "stop_type": "DROP_OFF"
    },
    {
      "sequence": 2,
      "address": "789 Nguyễn Văn Linh, Tân Phong, Quận 7, TP. Hồ Chí Minh",
      "latitude": 10.7294,
      "longitude": 106.7001,
      "contact_name": "Pham Van C",
      "contact_phone": "+84909888777",
      "stop_type": "DROP_OFF"
    }
  ]
}
```

- **Response (201 Created):**
```json
{
  "booking_id": "bk_987654321",
  "status": "CREATED",
  "created_at": "2026-06-16T07:15:30Z",
  "fare_details": {
    "base_fare": 250000,
    "distance_fare": 350000,
    "stop_surfaces_fare": 100000,
    "total_fare": 700000,
    "currency": "VND"
  },
  "stops": [
    {
      "stop_id": "bk_stop_101",
      "sequence": 0,
      "address": "Cảng Cát Lái, Thạnh Mỹ Lợi, Quận 2, TP. Hồ Chí Minh",
      "latitude": 10.7635,
      "longitude": 106.7992,
      "status": "PENDING"
    },
    {
      "stop_id": "bk_stop_102",
      "sequence": 1,
      "address": "12 Phan Chu Trinh, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
      "latitude": 10.7725,
      "longitude": 106.6980,
      "status": "PENDING"
    },
    {
      "stop_id": "bk_stop_103",
      "sequence": 2,
      "address": "789 Nguyễn Văn Linh, Tân Phong, Quận 7, TP. Hồ Chí Minh",
      "latitude": 10.7294,
      "longitude": 106.7001,
      "status": "PENDING"
    }
  ]
}
```

### 3.3. Xem chi tiết đơn đặt xe (Get Booking Details)
- **Endpoint:** `GET /bookings/{booking_id}`
- **Xác thực:** Yêu cầu (Bearer Token)
- **Response (200 OK):**
```json
{
  "booking_id": "bk_987654321",
  "status": "ASSIGNED",
  "driver": {
    "driver_id": "drv_8888",
    "full_name": "Trần Văn Tài",
    "phone_number": "+84900111222",
    "plate_number": "51C-999.99",
    "avatar_url": "https://cdn.leopard.vn/avatars/drv_8888.png"
  },
  "fare_details": {
    "total_fare": 700000,
    "currency": "VND",
    "is_paid": false
  },
  "tracking_token": "track_token_abc123xyz789",
  "created_at": "2026-06-16T07:15:30Z"
}
```

---

## 4. Tính toán cước phí & Thanh toán (Billing & VietQR)

### 4.1. Tính toán giá cước tạm tính (Fare Calculation)
Tính cước phí dựa trên khoảng cách đi được, số lượng điểm dừng, loại xe và các phụ phí khác.

- **Endpoint:** `POST /billing/calculate-fare`
- **Xác thực:** Yêu cầu (Bearer Token)
- **Request Body:**
```json
{
  "truck_type": "2.5_ton_covered",
  "total_distance_meters": 32500,
  "number_of_stops": 3,
  "has_loading_service": true,
  "is_night_trip": false
}
```

- **Response (200 OK):**
```json
{
  "base_fare": 250000,
  "distance_fare": 350000,
  "stops_charge": 100000,
  "loading_charge": 150000,
  "night_sur_charge": 0,
  "subtotal": 850000,
  "discount": 50000,
  "total_fare": 800000,
  "currency": "VND"
}
```

### 4.2. Khởi tạo mã VietQR thanh toán (Generate VietQR Payload)
Tạo mã QR động tiêu chuẩn Napas247 giúp khách hàng thực hiện chuyển khoản nhanh bằng ứng dụng ngân hàng.

- **Endpoint:** `POST /billing/payments/vietqr`
- **Xác thực:** Yêu cầu (Bearer Token)
- **Request Body:**
```json
{
  "booking_id": "bk_987654321",
  "amount": 800000,
  "description": "LEOPARD BK987654321",
  "bank_bin": "970415",
  "account_number": "19035678901234",
  "account_name": "CONG TY TNHH LEOPARD LOGISTICS"
}
```
*Ghi chú: `bank_bin` 970415 tương ứng với Ngân hàng Techcombank.*

- **Response (200 OK):**
```json
{
  "booking_id": "bk_987654321",
  "amount": 800000,
  "description": "LEOPARD BK987654321",
  "vietqr_raw_string": "00020101021238580010A000000727012400069704150114190356789012340208QRIBFTTA530370454068000005802VN5929LEOPARD LOGISTICS COMPANY LTD6007DA NANG62230819LEOPARD BK9876543216304D1B2",
  "vietqr_image_url": "https://img.vietqr.io/image/970415-19035678901234-compact.jpg?amount=800000&addInfo=LEOPARD%20BK987654321&accountName=CONG%20TY%20TNHH%20LEOPARD%20LOGISTICS",
  "status": "PENDING"
}
```

---

## 5. Dự đoán thời gian đến bằng AI (AI ETA)

Sử dụng AI kết hợp các dữ liệu thời gian thực để đưa ra dự báo chính xác về thời gian hoàn thành chặng đi (ETA).

- **Endpoint:** `POST /eta/predict`
- **Xác thực:** Yêu cầu (Bearer Token)
- **Request Body:**
```json
{
  "origin": {
    "latitude": 10.7635,
    "longitude": 106.7992
  },
  "destination": {
    "latitude": 10.7725,
    "longitude": 106.6980
  },
  "departure_time": "2026-06-16T08:00:00Z",
  "truck_type": "2.5_ton_covered",
  "ai_features": {
    "weather_condition": "heavy_rain",
    "historical_congestion_index": 0.75,
    "driver_experience_months": 24,
    "cargo_weight_kg": 1500,
    "estimated_loading_duration_minutes": 25
  }
}
```

- **Response (200 OK):**
```json
{
  "predicted_duration_minutes": 48.5,
  "predicted_arrival_time": "2026-06-16T08:48:30Z",
  "confidence_score": 0.92,
  "factors_applied": {
    "traffic_delay_minutes": 12.0,
    "weather_delay_minutes": 8.5,
    "loading_time_added": 25.0
  }
}
```

---

## 6. Theo dõi thời gian thực qua WebSockets (Real-time Tracking WSS)

Hệ thống cung cấp kết nối WebSocket để cập nhật tọa độ liên tục từ tài xế và đẩy trạng thái chuyến đi đến khách hàng thời gian thực.

- **WebSocket URL:** `wss://api.leopard.vn/ws/v1/tracking?token=<JWT_TOKEN>`
- **Phương thức xác thực:** Token được truyền trực tiếp qua query parameter `token`.

### 6.1. Chi tiết các sự kiện từ Client gửi lên Server (Client-to-Server Events)

#### 6.1.1. Cập nhật vị trí tài xế (DRIVER_LOCATION_UPDATE)
Tài xế định kỳ gửi vị trí địa lý của mình về hệ thống (mỗi 10 giây).

```json
{
  "event": "DRIVER_LOCATION_UPDATE",
  "payload": {
    "booking_id": "bk_987654321",
    "driver_id": "drv_8888",
    "latitude": 10.7689,
    "longitude": 106.7012,
    "speed_kph": 38.5,
    "bearing": 120.4,
    "timestamp": "2026-06-16T08:10:00Z"
  }
}
```

#### 6.1.2. Xác nhận đã đến điểm dừng (DRIVER_ARRIVED_AT_STOP)
Tài xế bấm nút xác nhận khi đã tới điểm dừng để hệ thống bắt đầu tính giờ load/unload hàng.

```json
{
  "event": "DRIVER_ARRIVED_AT_STOP",
  "payload": {
    "booking_id": "bk_987654321",
    "stop_id": "bk_stop_102",
    "timestamp": "2026-06-16T08:25:00Z"
  }
}
```

### 6.2. Chi tiết các sự kiện từ Server đẩy về Client (Server-to-Client Events)

#### 6.2.1. Đẩy vị trí tài xế tới Khách hàng (PUSH_DRIVER_LOCATION)
Được phát tới ứng dụng của khách hàng để hiển thị vị trí xe tải di chuyển trên bản đồ thời gian thực.

```json
{
  "event": "PUSH_DRIVER_LOCATION",
  "payload": {
    "booking_id": "bk_987654321",
    "latitude": 10.7689,
    "longitude": 106.7012,
    "speed_kph": 38.5,
    "bearing": 120.4,
    "last_updated": "2026-06-16T08:10:05Z"
  }
}
```

#### 6.2.2. Đẩy cập nhật dự đoán thời gian đến AI mới nhất (PUSH_AI_ETA_UPDATE)
Hệ thống AI tự động chạy ngầm, tính toán lại thời gian dựa trên vị trí hiện tại của tài xế và mật độ giao thông tức thời rồi phát bản tin này về cho cả Tài xế lẫn Khách hàng.

```json
{
  "event": "PUSH_AI_ETA_UPDATE",
  "payload": {
    "booking_id": "bk_987654321",
    "next_stop_id": "bk_stop_102",
    "eta_arrival_time": "2026-06-16T08:28:15Z",
    "remaining_distance_meters": 1200,
    "remaining_duration_minutes": 8.25
  }
}
```

#### 6.2.3. Thay đổi trạng thái chuyến đi (PUSH_BOOKING_STATUS_CHANGE)
Khi trạng thái booking thay đổi hoặc tài xế nhấn xác nhận qua các điểm dừng.

```json
{
  "event": "PUSH_BOOKING_STATUS_CHANGE",
  "payload": {
    "booking_id": "bk_987654321",
    "status": "IN_TRANSIT",
    "current_stop_sequence": 1,
    "updated_at": "2026-06-16T08:12:00Z"
  }
}
```

---

## 7. Các bảng mã lỗi hệ thống (Standard Error Codes)

| Mã lỗi (Error Code) | Trạng thái HTTP | Ý nghĩa (Description) |
|---|---|---|
| `UNAUTHORIZED` | 401 | Token không hợp lệ hoặc đã hết hiệu lực. |
| `FORBIDDEN` | 403 | Không có quyền truy cập tài nguyên này. |
| `BOOKING_NOT_FOUND` | 404 | Đơn hàng không tồn tại trên hệ thống. |
| `DRIVER_UNAVAILABLE` | 409 | Tài xế đã bận chuyến đi khác hoặc không hoạt động. |
| `OR_TOOLS_TIMEOUT` | 504 | Tiến trình tối ưu lộ trình bị quá thời gian xử lý. |
| `VIETQR_GATEWAY_ERROR` | 502 | Không thể kết nối với dịch vụ ngân hàng hoặc cổng Napas. |
