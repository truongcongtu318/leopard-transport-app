# ADR-003: Giải pháp Bản đồ (GIS), Định tuyến và Navigation Truck-Friendly

| Field | Value |
|---|---|
| **ID** | ADR-003 |
| **Tiêu đề** | Giải pháp Bản đồ (GIS), Định tuyến và Navigation Truck-Friendly |
| **Ngày** | 2026-06-15 |
| **Trạng thái** | Approved |
| **Tác giả** | Tech Lead Team LEOPARD |
| **Stakeholders** | Product Owner, Dev Team, GIS Specialist |
| **Phiên bản** | 2.0 |

---

## 1. BỐI CẢNH (Context)

Dự án LEOPARD yêu cầu một hệ thống bản đồ (GIS) và định tuyến (Routing) có các tính năng đặc thù:
1. **Map Rendering:** Hiển thị bản đồ trên Mobile (Flutter) và Web (Dashboard). Cho phép vẽ polyline (tuyến đường), marker (vị trí xe, điểm giao/nhận).
2. **Truck-Friendly Routing:** Định tuyến tránh các điểm cấm xe tải (giờ cấm, tải trọng cấm, chiều cao cầu thấp, cầu cấm tải trọng). Đây là yêu cầu cực kỳ quan trọng đối với xe tải lớn tại Việt Nam, đặc biệt ở các đô thị như Hà Nội, TP.HCM.
3. **Geocoding & Autocomplete:** Tìm kiếm địa chỉ từ chuỗi text ("123 Nguyễn Trãi") và ngược lại (Reverse Geocoding).
4. **Real-time Tracking & Distance Matrix:** Tính toán khoảng cách/thời gian nhanh từ nhiều tài xế đến 1 điểm nhận hàng (Distance Matrix API) và vẽ lộ trình xe di chuyển thực tế.

### Các ràng buộc đặc biệt tại Việt Nam:
- **Dữ liệu biển cấm:** Các API nước ngoài (Google, Mapbox) thường không cập nhật đầy đủ biển báo cấm tải, cấm giờ, chiều cao tĩnh không tại các tuyến đường đô thị Việt Nam.
- **Chi phí API:** Google Maps API (Direction, Distance Matrix, Places) cực kỳ đắt đỏ ($5 - $10/1000 requests), có thể làm cạn kiệt ngân sách 15M VND của dự án demo rất nhanh nếu test nhiều.

---

## 2. CÁC PHƯƠNG ÁN ĐÃ XEM XÉT (Alternatives Considered)

### Phương án A: Tự build OSRM (Open Source Routing Machine) với OpenStreetMap data + Custom Truck Profile
Tự deploy instance OSRM trên VPS Cloud, sử dụng dữ liệu bản đồ Việt Nam (.osm.pbf) từ Geofabrik, tùy biến profile định tuyến bằng Lua script để tránh cầu thấp/cấm tải.

| Tiêu chí | Đánh giá |
|---|---|
| **Chi phí** | **Miễn phí hoàn toàn** (chỉ tốn chi phí thuê VPS chạy OSRM instance ~150K-200K VND/tháng) |
| **Độ tùy biến** | **Tối đa** — Có thể viết script Lua (`truck.lua`) định nghĩa cấm đường |
| **Hiệu năng** | Cực kỳ nhanh |
| **Rủi ro** | OSM data tại Việt Nam chưa cập nhật 100% biển báo cấm tải trọng. |

### Phương án B: Sử dụng VIETMAP Maps API (Commercial Local Provider) — Recommended
Sử dụng dịch vụ API bản đồ của Vietmap dành cho developer Việt Nam.

| Tiêu chí | Đánh giá |
|---|---|
| **Độ chính xác** | **Cao nhất tại Việt Nam** — Dữ liệu biển cấm tải, cấm giờ, cầu thấp được cập nhật liên tục thực tế tại Việt Nam |
| **Tích hợp** | Dễ dàng (hỗ trợ REST API tiêu chuẩn, SDK Flutter/Web tương thích tốt) |
| **Chi phí (Free Tier)** | **Cực tốt cho demo** — Có gói **Trải nghiệm miễn phí trong 2 tháng** (< 60.000 transactions/tháng). Bao gồm: Tile Map (1.000 trans/ngày), Geocoding (500 trans/ngày), Reverse (500 trans/ngày), Autocomplete (500 trans/ngày), Routing (500 trans/ngày) |
| **Chi phí (Paid Tier)** | Có phí từ tháng thứ 3 (~50đ/transaction cho block đầu tiên) |

### Phương án C: Google Maps Platform API
Sử dụng bộ công nghệ của Google (Maps SDK, Directions API, Distance Matrix, Places API).

| Tiêu chí | Đánh giá |
|---|---|
| **Map Rendering** | Tốt nhất, mượt nhất |
| **Truck Routing** | **Không hỗ trợ** tại Việt Nam (không cấu hình được tải trọng, chiều cao xe tải) |
| **Chi phí** | Cực kỳ đắt |

---

## 3. QUYẾT ĐỊNH (Decision)

> **Chọn phương án Hybrid (Kết hợp Phương án A và Phương án B):**
> 
> 1. **Địa chỉ & Tìm kiếm (Autocomplete, Geocoding, Reverse):** Dùng trực tiếp **Vietmap Maps API (Free Tier 2 tháng)** vì Vietmap có cơ sở dữ liệu địa chỉ Việt Nam chính xác nhất (bao gồm cả số nhà, ngõ hẻm nhỏ) và cơ chế gợi ý autocomplete thông minh tiếng Việt.
> 2. **Map Rendering (Flutter Map):** Dùng `flutter_map` (OpenStreetMap) kết hợp với **Vietmap Tile Map API (1.000 trans/ngày free)** hoặc Mapbox Vector Tiles để có giao diện bản đồ Việt Nam mượt mà, đầy đủ tên đường chi tiết.
> 3. **Routing & Distance Matrix Engine (VRP & ETA):**
>    - Giai đoạn **Phát triển & Demo (Free Tier)**: Dùng **Vietmap Routing API** (500 trans/ngày) làm core routing cho việc tìm đường đi thực tế của xe tải và gọi Distance Matrix.
>    - Giai đoạn **Tối ưu OR-Tools (Local computation)**: Vì thuật toán OR-Tools VRP có thể cần gọi Distance Matrix hàng nghìn lần trong lúc tính toán (vượt limit 500 trans/ngày của Vietmap), hệ thống sẽ sử dụng **Local OSRM Engine** chạy dưới local machine/development server để làm solver, sau khi có kết quả route tối ưu sẽ convert lại và hiển thị lên UI bằng Vietmap API.

### Cấu trúc Bản đồ & Định vị (Vietmap-centric Hybrid)

```
                              ┌───────────────────────────┐
                              │      Flutter Client       │
                              └─────────────┬─────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               │                            │                            │
      Vietmap Tile API            Vietmap Autocomplete          Vietmap Routing API
     (Map Rendering UI)           (Địa chỉ chính xác)           (Demo Route & ETA)
               │                            │                            │
               └────────────────────────────┼────────────────────────────┘
                                            │
                                  ┌─────────▼─────────┐
                                  │  FastAPI Backend  │
                                  └─────────┬─────────┘
                                            │
                                ┌───────────▼───────────┐
                                │   Celery Task (VRP)   │
                                │   (Local OSRM Solver  │
                                │    for Matrix computation)
                                └───────────────────────┘
```

---

## 4. HỆ QUẢ (Consequences)

### ✅ Tích cực (Positive)
1. **Dữ liệu Truck Routing & Địa chỉ chính xác 100%:** Vietmap là công ty Việt Nam đi đầu về bản đồ, đảm bảo việc dẫn đường tránh cấm tải, cấm giờ cực kỳ chính xác trong các khu vực đô thị phức tạp của Hà Nội và TP.HCM.
2. **Miễn phí hoàn toàn trong 2 tháng (giai đoạn Đồ án):** Gói free 60K trans/tháng dư sức phục vụ phát triển, test và bảo vệ tốt nghiệp trước hội đồng vào 15/9/2026.
3. **Dễ dàng tích hợp:** Không cần build OSRM server phức tạp ngay từ đầu, giảm thiểu rủi ro dev ops cho team. Chỉ cần gọi các REST API endpoint của Vietmap với Token.
4. **Hỗ trợ autocomplete tiếng Việt xuất sắc:** Nhập địa chỉ không dấu, viết tắt ("123 ng h thọ q7") vẫn gợi ý đúng địa điểm thực tế.

### ⚠️ Trung tính (Neutral)
1. Gói free giới hạn **500 routing trans/ngày** và **500 autocomplete trans/ngày**. Team cần viết code tối ưu caching (Redis cache kết quả route/address) để tiết kiệm transactions lúc test.
2. Cần đăng ký tài khoản console trên maps.vietmap.vn để lấy API Key trước khi bắt đầu code.

### ❌ Tiêu cực (Negative)

| Rủi ro | Impact | Mitigation |
|---|---|---|
| Hết 2 tháng free hoặc vượt giới hạn 500 trans/ngày trong lúc load test | Trung bình | Tự động fallback sang Local OSRM engine nếu API Vietmap trả về lỗi Over-Limit (HTTP 429) |
| Phí sau khi hết free tier cao đối với startup/SME thương mại | Thấp (chỉ làm đồ án tốt nghiệp) | Đồ án tốt nghiệp bảo vệ xong trước 15/9/2026 (nằm trong khung 2 tháng phát triển & demo). Nếu phát triển thương mại sau này, sẽ chuyển hẳn sang Hybrid OSRM tự host |

---

## 5. ĐIỀU KIỆN KIỂM TRA (Validation Criteria)

| # | Tiêu chí | Phương pháp kiểm tra | Ngưỡng chấp nhận |
|---|---|---|---|
| 1 | Vietmap API integration | Tạo connection test và query thử 1 route | Trả về JSON route polyline, HTTP 200 |
| 2 | Caching mechanism | Thực hiện query 1 route lặp lại 10 lần | Chỉ tốn 1 trans của Vietmap (9 lần sau lấy từ Redis cache) |
| 3 | Autocomplete địa chỉ | Search địa chỉ "98 xô viết nghệ tĩnh đà nẵng" | Trả về toạ độ chính xác của chi nhánh Vietmap Đà Nẵng |
| 4 | Fallback mechanism | Giả lập Vietmap API trả về HTTP 429 hoặc timeout | Hệ thống tự động chuyển sang gọi Local OSRM API trong < 1s |

---

## 6. THAM KHẢO (References)

- [Vietmap Maps API Console & Portal](https://maps.vietmap.vn/)
- [Vietmap API Price & Free Tier Statement](https://maps.vietmap.vn/web#pricingSection)
- [Vietmap API Documentation](https://maps.vietmap.vn/docs/)
- ADR-002 (Backend selection) — Kết nối API
- ADR-005 (AI ETA & VRP) — Kết hợp OSRM Local solver cho OR-Tools

---

## 7. LỊCH SỬ THAY ĐỔI (Changelog)

| Phiên bản | Ngày | Tác giả | Mô tả |
|---|---|---|---|
| 1.0 | 2026-06-15 | Tech Lead | Bản đầu tiên, chọn OSRM Custom + Goong API |
| 2.0 | 2026-06-15 | Tech Lead | Cập nhật chọn Vietmap Maps API (Free Tier 2 tháng) |
