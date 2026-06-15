# ADR-001: Lựa chọn Công nghệ Frontend cho Mobile & Web

| Field | Value |
|---|---|
| **ID** | ADR-001 |
| **Tiêu đề** | Lựa chọn Công nghệ Frontend cho Mobile & Web |
| **Ngày** | 2026-06-15 |
| **Trạng thái** | Approved |
| **Tác giả** | Tech Lead Team LEOPARD |
| **Stakeholders** | Product Owner, Dev Team, Hội đồng Đồ án |
| **Phiên bản** | 1.0 |

---

## 1. BỐI CẢNH (Context)

Dự án LEOPARD cần một ứng dụng client chạy trên nhiều nền tảng:
- **Mobile:** Android là bắt buộc (chiếm 85%+ thị phần tài xế và SMEs tại VN). iOS là nice-to-have cho khách hàng cao cấp.
- **Web:** Dashboard quản lý đội xe (Fleet Management) cho doanh nghiệp, truy cập từ desktop/laptop.

### Yêu cầu kỹ thuật bắt buộc
1. Hiển thị **bản đồ real-time** mượt mà (Map rendering & animation).
2. Tương tác **GPS tracking trực tiếp** (WebSocket/live location updates).
3. **Camera** chụp ảnh/video hàng hóa trực tiếp trong app.
4. **Push notification** (Firebase Cloud Messaging).
5. **Offline-first** (tối thiểu caching form đặt đơn khi mất mạng).
6. UI mượt 60fps trên điện thoại tầm trung (dòng Xiaomi/Samsung 4-6 triệu đồng).

### Ràng buộc dự án
- **Ngân sách:** 15M VND (không đủ cho 2 team Android + iOS riêng).
- **Thời gian:** < 12 tuần (trước 15/9/2026).
- **Nhân sự:** Sinh viên, khả năng học framework mới có AI Agent hỗ trợ.

---

## 2. CÁC PHƯƠNG ÁN ĐÃ XEM XÉT (Alternatives Considered)

### Phương án A: Flutter (Google)
**Framework đa nền tảng:** Dart language, compile native ARM code, single codebase cho Android + iOS + Web + Desktop.

| Tiêu chí | Đánh giá |
|---|---|
| **Map rendering** | Rất tốt — `flutter_map` + `google_maps_flutter` hoặc native Mapbox/Goong SDK qua PlatformView |
| **Hiệu năng** | Native ARM compile, 60fps smooth kể cả trên thiết bị thấp cấp |
| **Camera** | `camera` + `image_picker` package chính thức của Flutter team |
| **Push noti** | `firebase_messaging` chính thức, Firebase team maintain |
| **Web support** | Flutter Web (CanvasKit / HTML renderer), phù hợp cho dashboard admin |
| **Tài nguyên** | Pub.dev có >50,000 packages, community lớn, Google maintain |
| **AI Agent code** | Claude, GPT-4, Hermes viết Flutter/Dart rất tốt (Dart syntax tường minh, ít pattern rối hơn JSX) |
| **Rủi ro** | Team phải học Dart (~1 tuần) nếu chưa biết; Web SEO kém (không quan trọng với dashboard nội bộ) |

### Phương án B: React Native (Meta)
**Framework đa nền tảng:** JavaScript/TypeScript, bridge sang native qua Hermes engine.

| Tiêu chí | Đánh giá |
|---|---|
| **Map rendering** | Tạm ổn — `react-native-maps` (wrapper Google Maps SDK), nhưng animation phức tạp gây lag trên Android cấu hình thấp |
| **Hiệu năng** | JavaScript bridge overhead, có thể gặp frame drop ở scroll/bản đồ phức tạp |
| **Camera** | `react-native-camera` hoặc `expo-camera` — ổn định nhưng cấu hình phức tạp hơn Flutter |
| **Push noti** | `@react-native-firebase/messaging` — tốt |
| **Web support** | React Native for Web — chia sẻ code nhưng phải dùng thêm Next.js/Remix cho dashboard |
| **AI Agent code** | Viết được nhưng JSX dynamic typing dễ sinh bug runtime khó debug |
| **Rủi ro** | Dependencies npm rất dễ bị breaking changes; phải cấu hình native module phức tạp |

### Phương án C: Native (Android Kotlin + iOS Swift + Web React)
Hai codebase native riêng + Web dashboard bằng React riêng.

| Tiêu chí | Đánh giá |
|---|---|
| **Hiệu năng** | Tốt nhất từng nền tảng |
| **Rủi ro** | 3 codebase → cần ít nhất 3 developer riêng, vượt ngân sách & thời gian gấp 3 lần |
| **Thời gian** | Không khả thi trong 12 tuần với đội sinh viên |

### Phương án D: PWA (Progressive Web App)
Web app duy nhất chạy trên browser mobile.

| Tiêu chí | Đánh giá |
|---|---|
| **Camera + GPS** | Hạn chế — GPS background tracking không hoạt động, camera access bị giới hạn |
| **Push notification** | Không hỗ trợ trên iOS Safari, Android hỗ trợ hạn chế |
| **Kết luận** | Không đáp ứng được yêu cầu cốt lõi (live tracking, camera, notification) |

---

## 3. QUYẾT ĐỊNH (Decision)

> **Chọn Flutter (Phương án A)** làm công nghệ Frontend cho toàn bộ client application, bao gồm:
> - Mobile App (Android + iOS): Compile native qua Flutter SDK
> - Web Dashboard (Fleet Management): Flutter Web với CanvasKit renderer

### Chi tiết kỹ thuật

| Layer | Công nghệ | Lý do |
|---|---|---|
| **UI Framework** | Flutter 3.x (latest stable) | Single codebase, native compile |
| **State Management** | Riverpod 2.x | Compile-time safety, testable, hỗ trợ async native |
| **Routing** | GoRouter | Declarative routing, deep link, auth guard |
| **Map** | `google_maps_flutter` hoặc `mapbox_gl` (PlatformView) | Map native SDK for performance |
| **GPS Tracking** | `geolocator` + `background_fetch` | Foreground + background location |
| **WebSocket** | `web_socket_channel` | Live tracking connection |
| **Camera** | `camera` / `image_picker` | Chính thức từ Flutter team |
| **Push Notification** | `firebase_messaging` | Firebase Cloud Messaging tích hợp |
| **HTTP Client** | `dio` | Interceptors cho auth token refresh, retry, logging |
| **Local Storage** | `shared_preferences` + `hive` | Preferences + offline cache |
| **Code Generation** | `freezed` + `json_serializable` | Immutable models, auto-generate JSON serialization |
| **Testing** | `flutter_test` + `integration_test` | Widget test + e2e |

### Cấu trúc thư mục Flutter dự kiến

```
leopard_app/
├── lib/
│   ├── core/
│   │   ├── constants/      # Màu sắc, typography, API endpoints
│   │   ├── network/        # Dio client, interceptors, WebSocket
│   │   ├── storage/        # SharedPreferences, Hive wrappers
│   │   ├── theme/          # ThemeData, dark/light mode
│   │   └── utils/          # Helpers, formatters, extensions
│   ├── features/
│   │   ├── auth/           # Đăng ký, đăng nhập, xác thực
│   │   ├── order/          # Tạo đơn, danh sách đơn, chi tiết
│   │   ├── tracking/       # Bản đồ real-time, ETA
│   │   ├── payment/        # VietQR, COD, hóa đơn
│   │   ├── profile/        # Hồ sơ, giấy tờ
│   │   ├── business/       # Dashboard doanh nghiệp
│   │   └── notification/   # In-app notifications
│   ├── shared/
│   │   ├── widgets/        # Reusable UI components
│   │   └── models/         # Data models (freezed)
│   ├── router/             # GoRouter configuration
│   └── main.dart
├── test/                   # Unit tests + Widget tests
└── integration_test/       # E2E tests
```

---

## 4. HỆ QUẢ (Consequences)

### ✅ Tích cực (Positive)
1. **Single codebase** cho Android + iOS + Web → Tiết kiệm 70% thời gian code so với native.
2. **Hiệu năng native** → Bản đồ mượt, camera nhanh, GPS tracking không bị delay.
3. **AI Agent viết Dart rất tốt** → Claude và GPT-4 có khả năng sinh code Flutter chuẩn, có thể dùng AI Agent tạo tính năng nhanh gấp 5 lần.
4. **Hệ sinh thái Firebase** → Auth, Messaging, Crashlytics được Google maintain, tích hợp Flutter first-class.
5. **Riverpod** an toàn hơn Provider/BLoC về compile-time check, ít bug runtime hơn.

### ⚠️ Trung tính (Neutral)
1. Team cần học Dart và Flutter (~1 tuần nếu đã biết OOP). Đây là chi phí một lần, đầu tư tốt cho career sau này.
2. Flutter Web CanvasKit render → kích thước bundle lớn (~3-4MB) nhưng chấp nhận được cho dashboard nội bộ không cần SEO.
3. Không hỗ trợ Apple CarPlay / Android Auto trong giai đoạn đầu (không thuộc scope dự án).

### ❌ Tiêu cực (Negative)
1. Nếu Flutter có breaking change (hiếm, Google maintain tốt), migration có thể tốn thời gian.
2. Một số plugin bên thứ 3 (ví dụ Goong Map SDK cho Flutter) có thể cần viết Platform Channel riêng nếu không có package sẵn.
3. Web performance có thể không bằng React/Vue thuần → Nhưng chỉ dùng cho dashboard admin nội bộ, không phải public website.

### 🛡️ Mitigation cho rủi ro
- **Goong Map SDK:** Nếu không có package Flutter chính thức, dùng PlatformView wrapper Android/iOS native SDK hoặc fallback sang `google_maps_flutter`.
- **Flutter migration:** Pin Flutter SDK version trong CI/CD pipeline, kiểm tra compatibility trước khi upgrade.
- **Web perf:** Dùng HTML renderer thay vì CanvasKit nếu dashboard chủ yếu là table/form (lighter bundle).

---

## 5. ĐIỀU KIỆN KIỂM TRA (Validation Criteria)

| # | Tiêu chí | Phương pháp kiểm tra | Ngưỡng chấp nhận |
|---|---|---|---|
| 1 | App chạy trên Android 8+ | Test trên 5 thiết bị thật (Samsung, Xiaomi, Oppo) | Không crash, FPS bản đồ > 50 |
| 2 | Web Dashboard render chính xác | Cross-browser test Chrome, Edge, Firefox | UI nhất quán, không layout shift |
| 3 | Camera chụp ảnh hàng hóa | Integration test + manual test | Ảnh rõ nét, upload < 10s |
| 4 | GPS tracking real-time | E2E test mô phỏng di chuyển | Location update delay < 2s |
| 5 | AI Agent sinh code Flutter | Sinh 10 màn hình feature bằng Claude/GPT | Compile OK, chạy đúng flow |

---

## 6. THAM KHẢO (References)

- [Flutter Documentation](https://docs.flutter.dev/)
- [Riverpod Documentation](https://riverpod.dev/)
- [GoRouter Documentation](https://pub.dev/packages/go_router)
- [Flutter Map Performance](https://docs.flutter.dev/perf/rendering-performance)
- ADR-003 (GIS & Routing Engine) — Quyết định Map SDK

---

## 7. LỊCH SỬ THAY ĐỔI (Changelog)

| Phiên bản | Ngày | Tác giả | Mô tả |
|---|---|---|---|
| 1.0 | 2026-06-15 | Tech Lead | Bản đầu tiên, quyết định chọn Flutter |
