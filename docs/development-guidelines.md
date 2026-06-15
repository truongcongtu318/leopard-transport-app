# DEVELOPMENT GUIDELINES: WORKFLOW, CODE LAYOUT & TASK ALLOCATION
## DỰ ÁN: LEOPARD - HỆ THỐNG KẾT NỐI VẬN TẢI HÀNG HÓA TRỌNG TẢI LỚN

| Field | Value |
|---|---|
| **Tên tài liệu** | Hướng dẫn Phát triển, Cấu trúc Code & Phân chia Nhiệm vụ |
| **Dự án** | LEOPARD APP |
| **Phiên bản** | 1.0 |
| **Ngày tạo** | 2026-06-15 |
| **Tác giả** | Tech Lead Team LEOPARD |
| **Trạng thái** | Approved |

---

## 1. PHÂN CHIA NHIỆM VỤ CHI TIẾT (TASK ALLOCATION MATRIX)

Để dự án 2 người chạy mượt mà, công việc được tách biệt hoàn toàn theo lớp kiến trúc (Frontend vs Backend/AI). Dưới đây là bảng phân bổ chi tiết qua 5 giai đoạn phát triển (13 tuần) từ 15/06/2026 đến 15/09/2026:

### 1.1. Bảng phân chia vai trò chính
- **Dev A (Backend & AI/ML Specialist):** Chịu trách nhiệm thiết kế database, viết REST API, tích hợp Redis, viết các logic AI dự báo ETA (XGBoost), tích hợp Google OR-Tools (VRP), deploy Docker-compose và VPS.
- **Dev B (Frontend & Mobile/Web Developer):** Chịu trách nhiệm thiết kế Flutter UI/UX, tích hợp Firebase Client (Auth, FCM), tích hợp Vietmap Flutter SDK, xử lý logic offline cache, kết nối HTTP/WebSocket API từ Dev A, xây dựng dashboard web.

### 1.2. Phân chia Task qua các Sprint (Không chồng chéo)

| Sprint / Tuần | Nhiệm vụ của **Dev A (Backend & AI)** | Nhiệm vụ của **Dev B (Frontend & Web)** | Điểm Giao Thoa (Integration Point) |
|---|---|---|---|
| **Sprint 1**<br>(Tuần 1 - 2)<br>*Setup & Auth* | - Setup FastAPI skeleton, Docker Compose.<br>- Khởi tạo DB Schema (Alembic Migrations).<br>- Tích hợp Firebase Auth Admin SDK (Verify JWT Token).<br>- Viết API: Đăng nhập OTP, Google SSO, Profile. | - Khởi tạo Flutter Project (Clean Architecture skeleton).<br>- Tích hợp Firebase SDK (Auth, Phone login, Google Sign-in).<br>- Code giao diện Auth (Splash, Phone OTP, Google Login, Role Select). | **API Contract `/auth/*`**<br>Dev B dùng token sinh từ Firebase gửi lên API `/auth/verify` của Dev A để tạo session. |
| **Sprint 2**<br>(Tuần 3 - 5)<br>*Core CRUD & File* | - Viết API quản lý xe (Vehicles) & tài xế (Drivers).<br>- Viết API quản lý Giấy tờ (upload file lên Local Storage).<br>- Viết API Đặt đơn hàng (Orders) và các Stops.<br>- Setup Postgres triggers tự động audit log trạng thái. | - Code giao diện đăng ký tài xế (Upload hình GPLX, Cà vẹt, ảnh xe).<br>- Code giao diện Shipper: Đặt đơn đa điểm (Vietmap Autocomplete), nhập thông số hàng.<br>- Quản lý state UI bằng Bloc/Cubit. | **API Contract `/drivers/*`, `/orders/*`**<br>Tích hợp file upload (Multipart form) và API đặt đơn hàng đa điểm. |
| **Sprint 3**<br>(Tuần 6 - 8)<br>*Real-time & GIS* | - Setup WebSocket Handler trong FastAPI.<br>- Setup Redis Pub/Sub phục vụ real-time tracking.<br>- Tích hợp Vietmap Routing API phía backend (để tính distance ban đầu).<br>- Tích hợp Redis Geohash lưu vị trí driver. | - Tích hợp `flutter_map` hiển thị bản đồ.<br>- Kết nối WebSocket API lấy location xe.<br>- Viết logic render Marker xe tải di chuyển mượt (Lerp interpolation).<br>- Xử lý offline caching GPS local khi mất mạng. | **WebSocket Protocol & Vietmap Key**<br>Dev A định nghĩa JSON frame WebSocket gửi tọa độ tài xế, Dev B nhận và vẽ route polyline. |
| **Sprint 4**<br>(Tuần 9 - 10)<br>*AI & Optimization* | - Train model XGBoost dự báo ETA, build API endpoint predict.<br>- Viết Background Worker (Celery/RQ) giải OR-Tools VRP.<br>- Viết API gợi ý đơn ghép dọc đường về (Bids). | - Code màn hình Driver: Nhận đơn, Bản đồ Navigation (vẽ route tránh cấm tải).<br>- Code màn hình popup nhận đơn ghép (Bidding sheet).<br>- Code màn hình ETA đếm ngược. | **API Contract `/eta/predict`, `/bookings/optimize`**<br>Dev B gửi metadata xe lên API để Dev A tính toán route VRP tối ưu và phản hồi. |
| **Sprint 5**<br>(Tuần 11 - 12)<br>*Thanh toán & Web* | - Viết API VietQR sinh mã QR động (NAPAS specs).<br>- Viết REST API thống kê doanh thu cho Fleet Owner.<br>- Viết API / Notifications push Firebase Cloud Messaging. | - Code UI thanh toán hiển thị VietQR.<br>- Code giao diện Web Portal (Flutter Web) cho Doanh nghiệp: Dashboard charts, Fleet tracking map. | **API Contract `/billing/*`, Web Build**<br>Đồng bộ dữ liệu đối soát QR. Build Flutter Web deploy lên Docker. |
| **Sprint 6**<br>(Tuần 13)<br>*Bugfix & Deploy* | - Deploy production trên VPS Ubuntu.<br>- Cấu hình Nginx, SSL Let's Encrypt.<br>- Load test WebSocket (100 concurrents). | - Build APK/IPA release.<br>- Viết tài liệu hướng dẫn sử dụng.<br>- Test tổng thể luồng đi (End-to-End). | **System Integration**<br>Trỏ Flutter client trỏ IP/domain thật của VPS Dev A host. |

---

## 2. CẤU TRÚC THƯ MỤC CODE (CODEBASE LAYOUT)

Để AI Agent tự động code mà không sinh ra file rác hoặc nhầm folder, cấu trúc thư mục toàn dự án được chuẩn hóa như sau:

### 2.1. Backend (FastAPI Layered Architecture)
Nằm trong thư mục `/backend`. Sử dụng kiến trúc phân lớp hướng dịch vụ (Router-Service-Repository).

```
backend/
├── app/
│   ├── api/                    # API Routing Layer
│   │   ├── deps.py             # Dependency Injection (Auth, DB session)
│   │   └── v1/
│   │       ├── auth.py         # /auth endpoints
│   │       ├── bookings.py     # /bookings endpoints
│   │       ├── drivers.py      # /drivers endpoints
│   │       ├── payments.py     # /payments endpoints
│   │       └── websocket.py    # WebSocket connection manager
│   ├── core/                   # Cấu hình hệ thống
│   │   ├── config.py           # Đọc file env qua Pydantic Settings
│   │   ├── security.py         # JWT tokens & Password hashing
│   │   └── database.py         # Kết nối Async SQLAlchemy engine
│   ├── models/                 # Database Models (SQLAlchemy ORM)
│   │   ├── user.py
│   │   ├── order.py
│   │   ├── driver.py
│   │   └── payment.py
│   ├── schemas/                # Data Validation (Pydantic Schemas)
│   │   ├── user.py
│   │   ├── order.py
│   │   ├── driver.py
│   │   └── payment.py
│   ├── repositories/           # Database Queries (CRUD)
│   │   ├── base.py
│   │   ├── user_repo.py
│   │   └── order_repo.py
│   ├── services/               # Business Logic & Third Party APIs
│   │   ├── vietmap.py          # Gọi API Vietmap
│   │   ├── weather.py          # Gọi API OpenWeather
│   │   └── dynamic_pricing.py  # Tính tiền tự động
│   ├── workers/                # Background Tasks (Celery / RQ)
│   │   ├── tasks.py
│   │   └── vrp_solver.py       # Giải thuật OR-Tools VRP
│   ├── ml/                     # Machine Learning Models
│   │   ├── model.py            # Predictor XGBoost
│   │   └── train.py            # Script train offline
│   └── main.py                 # FastAPI Entrypoint
├── migrations/                 # Alembic Database Migrations
├── tests/                      # Unit & Integration Tests (Pytest)
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

### 2.2. Frontend (Flutter Clean Architecture simplified)
Nằm trong thư mục `/frontend`. Chia code theo tính năng (features), mỗi feature chia 3 lớp: data, domain, presentation.

```
frontend/
├── assets/                     # Images, Fonts, Configs
├── lib/
│   ├── core/                   # Shared Code & Utilities
│   │   ├── network/            # HTTP Client (Dio), WebSocket Client
│   │   ├── theme/              # Colors, Text Styles
│   │   └── utils/              # Helper functions
│   ├── features/               # Modules chức năng độc lập
│   │   ├── auth/               # Đăng nhập, Profile
│   │   ├── booking/            # Tạo đơn, Chọn xe, Thanh toán
│   │   ├── tracking/           # Bản đồ tracking realtime, chat
│   │   └── fleet_dashboard/    # Dashboard cho web
│   │       # Mỗi feature chứa 3 lớp (simplified):
│   │       ├── data/           # Models, DataSources (gọi API)
│   │       ├── domain/         # Repositories Interface, UseCases
│   │       └── presentation/   # BLoC/Cubit, Pages, Widgets UI
│   ├── main.dart               # Flutter Entrypoint
│   └── app.dart                # MaterialApp & Routing config
├── test/                       # Unit & Widget Tests
├── pubspec.yaml
└── web/                        # Flutter Web index template
```

---

## 3. QUY TRÌNH PHÁT TRIỂN VỚI AI & GIT (AI-ASSISTED GIT WORKFLOW)

Quy tắc này bắt buộc cả 2 lập trình viên và AI Agent phải tuân thủ để tránh xung đột mã nguồn.

### 3.1. Phân nhánh Git (Branching Strategy)
- **`main`**: Nhánh ổn định cao nhất, chỉ chứa code đã qua test và có thể chạy được trên production server.
- **`dev`**: Nhánh tích hợp chính. Mọi dev branch đều checkout từ `dev` và merge ngược lại `dev` thông qua Pull Request.
- **`feature/xxx`**: Nhánh phát triển tính năng mới (ví dụ: `feature/auth-otp`, `feature/vietmap-routing`).
- **`bugfix/xxx`**: Nhánh sửa lỗi phát sinh khẩn cấp.

### 3.2. Luồng làm việc với AI Agent (AI Agent Guardrails)
Khi gọi AI Agent thực hiện một task, dev phải yêu cầu agent tuân thủ:
1. **Locate first:** Luôn định vị file cần sửa bằng tool `search_files` trước khi edit, không tự tạo file trùng lặp.
2. **Minimally invasive:** Chỉ patch (`patch` tool) những dòng cần thiết. Không dùng `write_file` để ghi đè cả file lớn trừ khi file đó hoàn toàn mới.
3. **Local Lint & Test:**
   - Với Backend: Chạy linter (`flake8 .` hoặc `black --check .`) và pytest trước khi commit.
   - Với Frontend: Chạy `flutter analyze` và `flutter test` trước khi commit.
4. **Commit Msg:** Commit message bắt buộc sử dụng Conventional Commit (ví dụ: `feat(auth): add google login endpoint`).

---

## 4. TỰ ĐỘNG HÓA KIỂM THỬ (CI/CD PIPELINE WORKFLOW)

Để đảm bảo code không bị lỗi khi merge, chúng ta dùng GitHub Actions chạy tự động.

### 4.1. File cấu hình CI Backend (`.github/workflows/backend-ci.yml`)

```yaml
name: Backend CI (FastAPI)

on:
  push:
    branches: [ main, dev ]
    paths:
      - 'backend/**'
  pull_request:
    branches: [ main, dev ]
    paths:
      - 'backend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt pytest httpx flake8 black

      - name: Lint with flake8 (Syntax check)
        run: |
          cd backend
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      - name: Run Pytest
        run: |
          cd backend
          pytest
```

### 4.2. File cấu hình CI Frontend (`.github/workflows/frontend-ci.yml`)

```yaml
name: Frontend CI (Flutter)

on:
  push:
    branches: [ main, dev ]
    paths:
      - 'frontend/**'
  pull_request:
    branches: [ main, dev ]
    paths:
      - 'frontend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Java (For Flutter build dependencies)
        uses: actions/setup-java@v3
        with:
          distribution: 'zulu'
          java-version: '17'

      - name: Set up Flutter
        uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.19.x'

      - name: Install dependencies
        run: |
          cd frontend
          flutter pub get

      - name: Run Flutter Analyze (Linter)
        run: |
          cd frontend
          flutter analyze

      - name: Run Flutter Test (Unit tests)
        run: |
          cd frontend
          flutter test
```
