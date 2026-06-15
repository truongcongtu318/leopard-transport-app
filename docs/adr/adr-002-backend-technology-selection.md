# ADR-002: Lựa chọn Tech Stack cho Backend & Integration

| Field | Value |
|---|---|
| **ID** | ADR-002 |
| **Tiêu đề** | Lựa chọn Tech Stack cho Backend & Integration |
| **Ngày** | 2026-06-15 |
| **Trạng thái** | Approved |
| **Tác giả** | Tech Lead Team LEOPARD |
| **Stakeholders** | Product Owner, Dev Team, Data Engineer, AI Engineer |
| **Phiên bản** | 1.0 |

---

## 1. BỐI CẢNH (Context)

LEOPARD cần một Backend Server đảm nhiệm các vai trò chính:

### Module chức năng của Backend
1. **API Gateway & Authentication:** Xác thực (JWT, Firebase Auth), authorization (RBAC cho shipper vs driver vs doanh nghiệp), rate limiting, request logging.
2. **Order Management:** CRUD đơn hàng, lịch sử đơn, tìm kiếm, lọc, báo giá.
3. **Real-time Services:** WebSocket server làm trung gian cho GPS tracking (driver → server → shipper), chat giữa hai bên.
4. **AI/ML Engine:** XGBoost inference server cho ETA prediction; OR-Tools solver cho VRP tối ưu route.
5. **Payment Processing:** Sinh mã VietQR động, quản lý giao dịch COD.
6. **Dashboard API:** Aggregation dữ liệu cho Report & Analytics (fleet dashboard).
7. **Notification Service:** Quản lý push notification qua Firebase Cloud Messaging.

### Yêu cầu kỹ thuật
| Yêu cầu | Mô tả |
|---|---|
| **Concurrency** | WebSocket duy trì 500+ kết nối đồng thời (tài xế gửi location mỗi 3-5s) |
| **Latency** | API response < 200ms (95th percentile), WebSocket message latency < 500ms |
| **Tính toàn vẹn dữ liệu** | ACID transaction cho tạo đơn và thanh toán (không để lỗi double charge) |
| **Scalability** | Horizontal scaling khi mở rộng, không single point of failure |
| **Chi phí** | Open-source stack, deploy trên VPS giá rẻ (~300K VND/tháng giai đoạn prototype) |
| **AI Integration** | Gọi Python-native thư viện (XGBoost, OR-Tools, Scikit-learn) không qua REST proxy |

### Ràng buộc
- **Ngân sách:** 15M VND.
- **Team:** Backend developer có thể là sinh viên chưa có kinh nghiệm production.
- **Time-to-market:** 12 tuần.
- **AI Agent hỗ trợ:** Backend code cần dễ sinh bởi AI Agent, syntax rõ ràng, ít boilerplate.

---

## 2. CÁC PHƯƠNG ÁN ĐÃ XEM XÉT (Alternatives Considered)

### Phương án A: Python FastAPI (Recommended)

| Tiêu chí | Đánh giá |
|---|---|
| **Async I/O** | Nền tảng async (asyncio + starlette), WebSocket first-class support qua `WebSocketEndpoint` |
| **AI/ML Integration** | **Lợi thế tuyệt đối** — XGBoost, OR-Tools, Scikit-learn, NumPy, Pandas đều là Python-native. Không cần inter-service call qua REST để gọi model |
| **WebSocket** | FastAPI có built-in WebSocket support, dễ dàng scale với workers |
| **Performance** | So sánh với các Python framework khác: FastAPI > Flask (10-20x requests/s), tương đương với Node.js ở benchmark cơ bản |
| **Validation** | Pydantic v2 — compile-time type check, tự động gen OpenAPI spec, validate request body tự động |
| **Documentation** | Tự động sinh OpenAPI (Swagger UI + ReDoc) từ type hints — zero effort docs |
| **Package Ecosystem** | 250K+ packages trên PyPI |
| **Community** | 70K+ GitHub stars, maintain bởi tác giả Sebastián Ramírez (Tiangolo), release đều đặn |
| **AI Agent code** | Python là ngôn ngữ được AI Agent hỗ trợ tốt nhất (GPT-4, Claude, Copilot đều xuất sắc với Python) |
| **Learning curve** | Team cần biết Python nhưng FastAPI dễ học, tài liệu xuất sắc |

### Phương án B: Node.js (NestJS / Express)

| Tiêu chí | Đánh giá |
|---|---|
| **Async I/O** | Single-threaded event loop — WebSocket qua `socket.io` hoặc `ws` package |
| **AI/ML Integration** | **Weak point** — XGBoost, OR-Tools yêu cầu child process gọi Python subprocess hoặc REST API riêng. Thêm 1 service architecture complexity |
| **Type Safety** | TypeScript giúp code an toàn hơn JavaScript thuần, nhưng NestJS decorator-based có learning curve |
| **Performance** | Tốt cho I/O-bound tasks, nhưng CPU-bound (OR-Tools solve) sẽ block event loop |
| **AI Agent code** | Tốt, nhưng TypeScript generic types + decorators có thể làm AI Agent sinh code sai kiểu dễ dàng |

### Phương án C: Go (Gin / Fiber)

| Tiêu chí | Đánh giá |
|---|---|
| **Performance** | Tốt nhất trong các lựa chọn — native compile, goroutines cho concurrency |
| **AI/ML Integration** | **Rủi ro cao** — AI thư viện chủ yếu Python, Go phải gọi REST API hoặc gRPC sang Python service |
| **Learning curve** | Đội ngũ sinh viên mới học Go → rủi ro tiến độ cao |
| **AI Agent code** | Kém hơn Python — AI Agent sinh Go code ít hơn nhiều, dễ sai pattern |

### Phương án D: Java Spring Boot

| Tiêu chí | Đánh giá |
|---|---|
| **Performance** | JVM khởi động chậm, memory footprint cao (~500MB baseline) |
| **Development Speed** | Boilerplate-heavy, XML/annotation quá nhiều → production code dài gấp 2x Python |
| **AI/ML Integration** | Java không có XGBoost/OR-Tools binding ổn định → phải gọi REST Python service |
| **Kết luận** | Quá nặng cho dự án này, không phù hợp với budget và thời gian |

---

## 3. QUYẾT ĐỊNH (Decision)

> **Chọn Python FastAPI (Phương án A)** làm Backend Framework.
> 
> **Lý do quyết định:** LEOPARD yêu cầu tích hợp sâu với AI/ML (XGBoost ETA, OR-Tools VRP) — những thư viện này đều là Python-native. Việc chọn Node.js hoặc Go sẽ buộc team phải xây dựng thêm một Python microservice riêng cho AI, tăng gấp đôi độ phức tạp kiến trúc và thời gian deploy. FastAPI cho phép chạy cả API logic + AI inference trong cùng một process, giảm latency và complexity.

### Kiến trúc Backend chi tiết

```
┌─────────────────────────────────────────────────────┐
│                   LEOPARD Backend                     │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   FastAPI    │  │  AI Worker   │  │   Celery   │  │
│  │  (API Layer) │  │ (ETA + VRP)  │  │  (Async)   │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬───────┘  │
│         │                 │                 │          │
│  ┌──────▼─────────────────▼─────────────────▼───────┐  │
│  │               Message Queue (Redis)              │  │
│  └────────────────────────┬────────────────────────┘  │
│                           │                            │
│  ┌────────────────────────▼────────────────────────┐  │
│  │                  PostgreSQL                      │  │
│  │        (Main Database + TimescaleDB ext)         │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  ┌────────────────┐  ┌────────────────────────────┐  │
│  │  Redis Cache    │  │  Firebase Admin SDK        │  │
│  │  (Session +     │  │  (Auth + FCM + Crashlytics)│  │
│  │   Rate Limit +  │  └────────────────────────────┘  │
│  │   Pub/Sub)      │                                   │
│  └────────────────┘                                    │
└─────────────────────────────────────────────────────┘
```

### Công nghệ chi tiết từng thành phần

| Thành phần | Công nghệ | Version | Lý do |
|---|---|---|---|
| **Web Framework** | FastAPI | 0.111.x | Async, Pydantic v2, auto OpenAPI, WebSocket built-in |
| **Python Runtime** | Python 3.11+ | 3.11.15 | 3.11 nhanh hơn 3.10 ~60%, walrus operator, exception groups |
| **ASGI Server** | Uvicorn + Gunicorn | latest | Production-grade, worker pool, graceful shutdown |
| **ORM** | SQLAlchemy 2.0 + asyncpg | 2.0.x | Async PostgreSQL driver, native async/await |
| **Migrations** | Alembic | 1.13.x | Version-controlled DB schema, auto-generation from models |
| **Validation** | Pydantic v2 | 2.7.x | 5-50x faster than v1, Rust-based core (`pydantic-core`) |
| **WebSocket** | FastAPI WebSocket + `redis-pubsub` | built-in | Location tracking broadcast, shipper-subscriber pattern |
| **DB - Main** | PostgreSQL 16 | 16.x | ACID, JSONB, TimescaleDB extension, GIS (PostGIS) |
| **Cache** | Redis 7 | 7.x | Session store, rate limiting, message broker, pub/sub |
| **Queue** | Celery (Redis broker) | 5.x | Async task cho VRP optimization (heavy CPU task) |
| **Auth** | Firebase Admin SDK + JWT | latest | Firebase Auth đăng ký SĐT/Google + JWT self-issued |
| **AI - ETA** | XGBoost (xgboost) | 2.x | Gradient boosting cho time-series prediction |
| **AI - Routing** | OR-Tools (ortools) | 9.x | Google constraint solver cho VRP optimization |
| **Data Science** | Pandas, NumPy, Scikit-learn | latest | Data preprocessing, feature engineering, evaluation metrics |
| **Documentation** | Auto-generated OpenAPI/Swagger | — | Zero-effort API docs từ FastAPI decorators |
| **Testing** | pytest + httpx + pytest-asyncio | latest | Async test support, pytest fixtures |
| **CI** | GitHub Actions | — | Auto test, lint, type check trên push/PR |

### File structure dự kiến

```
leopard-backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py          # Firebase verify + JWT issue
│   │   │   │   ├── orders.py        # CRUD orders + booking
│   │   │   │   ├── tracking.py      # WebSocket - location stream
│   │   │   │   ├── payments.py      # VietQR + COD
│   │   │   │   ├── drivers.py       # Driver management
│   │   │   │   ├── businesses.py    # Fleet dashboard API
│   │   │   │   ├── eta.py           # ETA prediction query
│   │   │   │   └── optimize.py      # VRP route optimization
│   │   │   └── dependencies.py      # Dependency injection (auth, db session)
│   │   └── websocket/
│   │       ├── tracking_handler.py   # WebSocket event handler
│   │       └── chat_handler.py       # In-app chat WebSocket
│   ├── core/
│   │   ├── config.py                # Pydantic Settings (env-based)
│   │   ├── security.py              # JWT encode/decode, Firebase verify
│   │   ├── database.py              # SQLAlchemy async engine + session
│   │   └── redis.py                 # Redis connection pool
│   ├── models/
│   │   ├── user.py                  # SQLAlchemy User model
│   │   ├── driver.py                # Driver profile + documents
│   │   ├── order.py                 # Order, OrderStop, OrderItem
│   │   ├── payment.py               # Payment transaction
│   │   ├── vehicle.py               # Vehicle info + constraints
│   │   └── business.py              # Business/Fleet account
│   ├── schemas/
│   │   ├── auth.py                  # Pydantic request/response schemas
│   │   ├── order.py
│   │   ├── tracking.py
│   │   └── payment.py
│   ├── services/
│   │   ├── auth_service.py          # Firebase Auth integration
│   │   ├── order_service.py         # Business logic - đặt hàng
│   │   ├── tracking_service.py      # Real-time location state machine
│   │   ├── payment_service.py       # VietQR generation + COD
│   │   ├── notification_service.py  # FCM push noti send
│   │   └── pricing_engine.py        # Dynamic pricing algorithm
│   ├── ai/
│   │   ├── eta_predictor.py         # XGBoost inference wrapper
│   │   ├── route_optimizer.py       # OR-Tools VRP solver
│   │   ├── features.py              # Feature engineering cho ETA
│   │   └── models/                  # Saved model files (.pkl, .json)
│       ├── tasks/
│   │   ├── celery_app.py            # Celery app configuration
│   │   └── optimize_task.py         # Async VRP optimization
│   └── main.py                      # FastAPI app instance
├── migrations/                       # Alembic migration scripts
│   ├── versions/
│   └── alembic.ini
├── tests/
│   ├── unit/
│   │   ├── test_eta_predictor.py
│   │   └── test_route_optimizer.py
│   ├── integration/
│   │   ├── conftest.py
│   │   ├── test_orders_api.py
│   │   └── test_tracking_ws.py
│   └── conftest.py                  # Global fixtures + test DB setup
├── scripts/
│   ├── seed_data.py                 # Mock data generation
│   └── train_eta_model.py           # ETA model training pipeline
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml           # API + Redis + PostgreSQL + Celery
├── .env.example
├── pyproject.toml                   # Dependencies, tool configs
├── pytest.ini
└── README.md
```

---

## 4. HỆ QUẢ (Consequences)

### ✅ Tích cực (Positive)
1. **AI/ML trong cùng process:** XGBoost ETA và OR-Tools VRP chạy trực tiếp trong Python, không qua REST proxy → latency thấp, ít điểm lỗi.
2. **Tự động sinh OpenAPI spec:** Frontend developer có thể dùng codegen từ spec → giảm manual contract sync.
3. **Tốc độ phát triển nhanh:** Python syntax đơn giản + FastAPI ít boilerplate + AI Agent viết Python xuất sắc.
4. **Chi phí vận hành thấp:** Python chạy ổn định trên VPS $5-10/tháng (DigitalOcean, VNG Cloud).
5. **Cộng đồng lớn:** FastAPI + SQLAlchemy + PostgreSQL là stack có lượng tài liệu và Stack Overflow answer cực kỳ phong phú.
6. **Pydantic v2 validation:** Phát hiện data malformed từ request layer ngay khi đến → không để data sai đi sâu vào business logic.

### ⚠️ Trung tính (Neutral)
1. **Python GIL (Global Interpreter Lock):** CPU-bound tasks (OR-Tools solve) không thể chạy song song trong cùng process. Mitigation: Celery worker process riêng cho VRP tasks.
2. **Team phải biết Python** — Nếu chỉ quen Java/C# mất ~1 tuần chuyển đổi. AI Agent giảm đáng kể thời gian này.
3. **WSGI vs ASGI confusion:** Team cần hiểu ASGI lifecycle (lifespan events, background tasks) để tránh lỗi resource leak.

### ❌ Tiêu cực (Negative)

| Rủi ro | Impact | Mitigation |
|---|---|---|
| **Python runtime performance** cho high-frequency API kém hơn Go/Rust | Trung bình | FastAPI async + connection pooling + Redis cache giảm tải DB query |
| **WebSocket scaling** với nhiều worker | Cao | Dùng Redis Pub/Sub làm backplane: worker A nhận location → publish → subscribe broadcast đến tất cả workers |
| **ORM overhead** SQLAlchemy cho complex queries | Trung bình | Dùng raw SQL với asyncpg cho queries phức tạp (báo cáo thống kê) |
| **Celery dependency** tăng độ phức tạp infra | Thấp | Docker compose chỉ add 1 Redis container + 1 Celery worker container |

---

## 5. ĐIỀU KIỆN KIỂM TRA (Validation Criteria)

| # | Tiêu chí | Phương pháp kiểm tra | Ngưỡng chấp nhận |
|---|---|---|---|
| 1 | API response time | Load test với Locust, 100 concurrent users | p95 < 200ms |
| 2 | WebSocket throughput | 200 WebSocket connections, mỗi kết nối gửi location 3s/lần | Latency < 500ms, không drop message |
| 3 | Auto-generated OpenAPI | Kiểm tra `/docs` endpoint | Tất cả endpoints hiển thị, schemas generate đúng |
| 4 | AI ETA inference | 1000 calls mock data | Latency < 100ms/call, MAE < 5 phút |
| 5 | OR-Tools VRP solve | 250 orders, 50 drivers | Solve time < 30s (background Celery task) |
| 6 | ACID transaction | Test tạo đơn + thanh toán đồng thời 10 requests | 0 trường hợp double charge |
| 7 | CI/CD pipeline | GitHub Actions | Build pass + test pass + lint pass |

---

## 6. THAM KHẢO (References)

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Celery + FastAPI Integration](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Pydantic v2 Performance](https://docs.pydantic.dev/latest/why/)
- [XGBoost Python Package](https://xgboost.readthedocs.io/)
- [OR-Tools VRP Guide](https://developers.google.com/optimization/routing/vrp)
- ADR-003 (GIS & Routing Engine) — Quyết định Map Service
- ADR-005 (AI & Optimization Architecture) — Chi tiết ETA & VRP

---

## 7. LỊCH SỬ THAY ĐỔI (Changelog)

| Phiên bản | Ngày | Tác giả | Mô tả |
|---|---|---|---|
| 1.0 | 2026-06-15 | Tech Lead | Bản đầu tiên, quyết định chọn Python FastAPI |
