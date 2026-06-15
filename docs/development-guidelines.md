# QUY TRÌNH PHÁT TRIỂN & HƯỚNG DẪN LÀM VIỆC VỚI AI (DEVELOPMENT GUIDELINES)
## DỰ ÁN: LEOPARD — KẾT NỐI VẬN TẢI HÀNG HÓA TRỌNG TẢI LỚN

| Field | Value |
|---|---|
| **Tên tài liệu** | Development Guidelines & AI Workflow |
| **Dự án** | LEOPARD APP |
| **Phiên bản** | 1.0 |
| **Ngày** | 2026-06-15 |
| **Tác giả** | Tech Lead Team LEOPARD |

---

## 1. NGUYÊN TẮC LÀM VIỆC CHUNG (GOLDEN RULES)

### 1.1. Phân chia công việc — 2 người + AI Agent

| Vai trò | AI Agent | Dev 1 (Flutter + API integration) | Dev 2 (Backend + AI/ML + DevOps) |
|---|---|---|---|
| **Auth & Profile** | ✍️ Code CRUD backend mẫu | 📱 Màn hình Login/OTP/Profile | 🔧 Firebase config, verify token |
| **Booking đa điểm** | ✍️ API Order + Pricing engine | 📱 Màn hình tạo đơn + tìm xe | 🔧 Vietmap autocomplete, caching |
| **Bản đồ + Tracking** | ✍️ WebSocket manager + Redis Pub/Sub | 📱 flutter_map + marker tracking | 🔧 GPS insert TimescaleDB, geofence |
| **AI ETA (XGBoost)** | ✍️ Model training pipeline + API wrapper | 📱 Hiển thị ETA countdown | 🔧 Train model, data pipeline |
| **OR-Tools VRP** | ✍️ Celery worker OR-Tools solve | 📱 UI đề xuất ghép đơn | 🔧 Ràng buộc tối ưu, cost matrix |
| **Thanh toán VietQR** | ✍️ Endpoint gen VietQR | 📱 Màn hình QR + hướng dẫn | 🔧 NAPAS format validation |
| **Fleet Dashboard** | ✍️ API Dashboard, aggregation queries | 🖥️ Flutter Web charts UI | 🔧 DB aggregation, cache |
| **Notifications** | ✍️ FCM dispatch + lưu lịch sử | 📱 Notification listener + deep link | 🔧 Firebase Cloud Messaging config |

### 1.2. AI Agent có thể làm gì?
AI Agent có thể **code gần như toàn bộ backend và khung frontend** (Boilerplate CRUD, schema, models, service logic, bussiness logic viết rõ), nhưng:
- **Có thể tự động:** API CRUD, Pydantic schemas, SQLAlchemy models, unit test mẫu, Dockerfile, GitHub Actions, routing, BLoC boilerplate.
- **Cần con người kiểm tra:** Thiết kế UI/UX thực tế (màu sắc, layout trên app), fine-tune model AI (XGBoost cần data thật), config tài khoản API Vietmap/Firebase, kiểm thử manual trên thiết bị thật.
- **Tuyệt đối không:** Đẩy API key/secret lên public repo (luôn dùng `.env` và cung cấp file `.env.example`).

### 1.3. Ngôn ngữ và coding style
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Black formatter (88 chars).
- **Frontend:** Dart 3.x, Flutter 3.x, flutter_bloc, flutter_map, Dio, JSON serialization.
- **Code comments:** Viết docstring (Google style) cho mọi service/public function.
- **Commit message:** Tiếng Việt (kèm emoji prefix): `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`.
- **Import ordering:** Standard library → Third-party → Local.

---

## 2. GIT BRANCHING STRATEGY (GitHub Flow mở rộng)

```
main (production-ready)
  └── dev (integration branch)
        ├── feature/auth               ← AI Agent hoặc Dev 1
        ├── feature/booking            ← AI Agent
        ├── feature/tracking           ← AI Agent
        ├── feature/eta-model          ← Dev 2
        ├── feature/vrp                ← Dev 2
        ├── feature/payment            ← AI Agent
        ├── feature/dashboard          ← AI Agent
        ├── fix/issue-xxx              ← Hotfix
        └── docs/xxx                   ← Tài liệu
```

### Quy tắc:
1. **Không bao giờ commit trực tiếp lên `main`** (trừ tài liệu Markdown).
2. Mỗi tính năng mới tạo nhánh từ `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/booking
   ```
3. Khi hoàn thành, tạo Pull Request vào `dev` và gán cho người kia review.
4. Merge `dev` vào `main` khi đã chạy ổn định (khoảng 1 tuần/lần).
5. AI Agent không tự động merge PR — phải có người approve.

### AI Agent Guardrails (quy tắc cho AI khi code):
1. **Đọc file trước khi edit:** Không bao giờ viết lại toàn bộ file nếu chỉ cần sửa một đoạn.
2. **Không hardcode secrets:** Luôn dùng `os.getenv()` hoặc cấu hình từ file `.env`.
3. **Chạy linter trước khi kết luận:** Backend: `black . && flake8`. Frontend: `dart analyze`.
4. **Commit nhỏ, tập trung:** Mỗi commit chỉ nên chứa 1 tính năng/logic duy nhất.
5. **Không xoá code của người khác:** Nếu cần thay đổi logic, ưu tiên thêm mới thay vì sửa/xoá code người khác đã viết.

---

## 3. QUY TRÌNH VIẾT CODE (CODING WORKFLOW)

```
1. Lấy task từ danh sách
       │
2. Tạo nhánh Git: feature/[tên tính năng]
       │
3. Đọc docs liên quan (SRS, API Contract, ERD)
       │
4. AI Agent viết code (Backend: route → schema → service → test)
   (Dev: Frontend: BLoC → page → widget → test)
       │
5. Chạy kiểm tra tại chỗ:
   ├── Backend:  black && flake8 && pytest
   └── Frontend: dart format && dart analyze && flutter test
       │
6. Nếu OK → git add, commit, push
   Nếu lỗi → sửa, quay lại bước 5
       │
7. Mở Pull Request vào dev → tag người kia review
```

### Checklist trước khi commit:
- [ ] Linter pass (`black`, `flake8`, `dart analyze`)
- [ ] Unit tests pass (`pytest`, `flutter test`)
- [ ] Không có secret/API key trong code
- [ ] Đã test thủ công với Swagger UI (backend) hoặc hot reload (frontend)
- [ ] import không dư thừa (kiểm tra bằng `autoflake`)

---

## 4. QUY TẮC ĐẶT TÊN & CODE CONVENTION

### Backend (Python)
| Quy tắc | Ví dụ |
|---|---|
| Tên file: snake_case | `order_service.py`, `vietmap_client.py` |
| Tên class: PascalCase | `OrderService`, `AuthRepository` |
| Tên function: snake_case | `get_nearby_drivers()`, `calculate_price()` |
| Tên biến: snake_case | `total_price`, `driver_list` |
| Tên route: lowercase + dash | `/api/v1/nearby-drivers` |
| Tên DB model: singular PascalCase | `class OrderStop(Base)` |
| Tên Pydantic schema: suffix + Read/Create/Update | `OrderCreate`, `OrderRead`, `OrderUpdate` |

### Frontend (Dart)
| Quy tắc | Ví dụ |
|---|---|
| Tên file: snake_case | `login_page.dart`, `booking_bloc.dart` |
| Tên class: PascalCase | `LoginPage`, `BookingBloc` |
| Tên function/method: camelCase | `onSubmit()`, `loadOrders()` |
| Tên biến: camelCase | `totalPrice`, `driverList` |
| Tên BLoC Event: PascalCase | `class LoadOrders extends BookingEvent` |
| Tên BLoC State: PascalCase | `class BookingLoaded extends BookingState` |
| Import package ordering: std → third → local | |

---

## 5. PHỐI HỢP REAL-TIME (COORDINATION BETWEEN TWO DEVS)

Vì dự án có 2 người làm song song, cần tránh conflict code:

### Quy tắc không conflict:
| Dev 1 (Frontend) | Dev 2 (Backend + AI) |
|---|---|
| Chỉ chỉnh sửa trong `leopard-frontend/` | Chỉ chỉnh sửa trong `leopard-backend/` |
| Models mock data (Dart) khi backend chưa xong | Service dùng Pydantic test backend logic |
| Giao tiếp qua API Contract (đã có) | Luôn giữ API Contract cập nhật |

### Khi AI Agent can thiệp:
AI Agent có thể code cả backend lẫn frontend. Nếu AI đang code backend, Dev 2 không sửa cùng file đó cùng lúc. Luôn **pull mới nhất** từ `dev` trước khi bắt đầu làm việc:

```bash
git checkout dev
git pull origin dev
git checkout -b feature/my-feature
```

---

## 6. THIẾT LẬP MÔI TRƯỜNG PHÁT TRIỂN (DEVELOPMENT SETUP)

### Lần đầu chạy:
```bash
# Backend
cd leopard-backend
cp ../.env.example ../.env    # Điền API keys thật vào .env
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
cp ../docker-compose.yml ../docker-compose.yml
# Chạy DB + Redis
docker compose up -d postgres redis
# Alembic migrations
alembic upgrade head
# Seed data
python scripts/seed_users.py
# Khởi động backend
uvicorn app.main:app --reload

# Frontend
cd ../leopard-frontend
flutter pub get
flutter run
```

### Hàng ngày:
```bash
# Luôn bắt đầu bằng pull dev mới nhất
git checkout dev && git pull origin dev

# Chạy DB nếu chưa chạy
docker compose up -d postgres redis

# Code...
# Khi xong, test
cd leopard-backend && black . && flake8 && pytest
cd ../leopard-frontend && dart analyze && flutter test

git push origin feature/my-feature
# Mở PR trên GitHub
```

---

## 7. XỬ LÝ TÌNH HUỐNG (TROUBLESHOOTING)

| Tình huống | Hành động |
|---|---|
| DB migration conflict | `alembic merge heads` tạo merge migration |
| Redis bị đầy bộ nhớ | `docker compose restart redis` (hoặc xoá `leopard_redis_data` volume) |
| Conflict Git khi merge | Git merge conflict → mở file conflict → giữ code của cả 2 → commit |
| AI Agent code sai logic | Revert commit cuối: `git revert HEAD` rồi báo AI sửa |
| Cần test với data thật | Chạy script `seed_gps_tracking.py` để sinh 1000 GPS points fake |
| API Key hết hạn | Kiểm tra `.env` → cập nhật key mới → `docker compose restart backend` |

---

## 8. HƯỚNG DẪN SỬ DỤNG AI HIỆU QUẢ

### Prompt template chuẩn khi yêu cầu AI Agent code:
```
## Task
Viết [chức năng gì] trong [backend/frontend]

## Context
- File liên quan: [đường dẫn]
- ERD table: [tên bảng]
- API endpoint: [method + path]
- Acceptance Criteria: [từ SRS]
- Docstring mẫu: ...

## Yêu cầu cụ thể
1. [yêu cầu 1]
2. [yêu cầu 2]

## Constraint
- Không hardcode secret
- Dùng async/await
- Viết unit test kèm theo
```

### Khi nào gọi AI Agent:
- **Nên gọi:** CRUD boilerplate, schema/model generation, test writing, tài liệu, simple service logic (pricing, validation).
- **Không nên gọi (tự làm):** Design UI layout, fine-tune ML model, config complex DevOps (Firebase project setup), quyết định kiến trúc.

---

## 9. REFERENCES

- [SRS](./srs.md) — Yêu cầu chức năng chi tiết
- [API Contract](./api-contract.md) — REST + WebSocket endpoints
- [ERD](./erd.md) — Database schema
- [Architecture Design](./architecture-design.md) — C4 diagrams, folder structure
- [Project Plan](./project-plan.md) — Milestones, timeline, risk register, budget
- [Test Plan](./test-plan.md) — Testing strategy, CI/CD
