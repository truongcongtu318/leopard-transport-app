# THIẾT KẾ KIẾN TRÚC HỆ THỐNG & CẤU TRÚC MÃ NGUỒN
## DỰ ÁN: LEOPARD — KẾT NỐI VẬN TẢI HÀNG HÓA TRỌNG TẢI LỚN

| Field | Value |
|---|---|
| **Tên tài liệu** | Architecture Design & Codebase Structure |
| **Dự án** | LEOPARD APP |
| **Phiên bản** | 1.0 |
| **Ngày** | 2026-06-15 |
| **Tác giả** | Tech Lead Team LEOPARD |

---

## 1. SƠ ĐỒ C4 — KIẾN TRÚC TỔNG THỂ (C4 Container Diagram)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LEOPARD SYSTEM — C4 Container                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐      ┌─────────────────────┐                       │
│  │  Mobile App          │      │  Web Portal          │                      │
│  │  (Flutter Android/iOS)│     │  (Flutter Web)       │                      │
│  │  - Shipper UI         │     │  - Enterprise Dashboard│                    │
│  │  - Driver UI          │     │  - Admin Portal       │                     │
│  └─────────┬─────────────┘      └──────────┬──────────┘                     │
│            │ HT TS/WSS                     │ HT TS/WSS                      │
│            └──────────────┬───────────────┘                                 │
│                           │                                                 │
│                    ┌──────▼──────┐                                          │
│                    │  FastAPI    │                                          │
│                    │  Backend    │                                          │
│                    │  Port:8000  │                                          │
│                    └──┬──┬───┬──┘                                          │
│                       │  │   │                                              │
│          ┌────────────┘  │   └────────────┐                                │
│          ▼               ▼                ▼                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                        │
│  │ PostgreSQL   │ │ Redis 7      │ │ External APIs│                        │
│  │ + PostGIS    │ │ Cache/PubSub │ │              │                        │
│  │ + TimescaleDB│ │ Rate Limit   │ │ Vietmap Maps │                        │
│  │ Port:5432    │ │ Port:6379    │ │ OpenWeather  │                        │
│  └──────────────┘ └──────────────┘ │ Firebase/Auth│                        │
│                                    └──────────────┘                        │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │ Background Workers (Celery + Redis Broker)                        │      │
│  │  ├── OR-Tools VRP Solver   (optimize_route task)                  │      │
│  │  ├── XGBoost ETA Predictor (predict_eta task)                     │      │
│  │  ├── GPS Archiver          (archive_gps_to_timescaledb task)      │      │
│  │  └── Notification Dispatcher (send_push notification task)        │      │
│  └──────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. CẤU TRÚC THƯ MỤC BACKEND (FastAPI — Clean Layered Architecture)

```
leopard-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry, middleware, lifespan
│   ├── config.py                    # Settings (pydantic-settings), env vars
│   │
│   ├── api/                         # REST API Layer
│   │   ├── __init__.py
│   │   ├── deps.py                  # Dependency injection (get_db, get_current_user)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py            # Aggregated API router
│   │       ├── auth.py              # POST /auth/phone/otp-*, POST /auth/google
│   │       ├── users.py             # GET/PUT /users/me, PUT /drivers/{id}/location
│   │       ├── orders.py            # POST /orders, GET /orders/{id}, GET /orders/search
│   │       ├── bidding.py           # POST /orders/{id}/bids, PUT /bids/{id}/accept
│   │       ├── payments.py          # POST /payments/vietqr
│   │       ├── tracking.py          # WebSocket /ws/tracking/{order_id}
│   │       ├── eta.py               # POST /eta/predict
│   │       ├── vrp.py               # POST /vrp/optimize
│   │       ├── notifications.py     # GET /notifications, PUT /notifications/{id}/read
│   │       ├── admin.py             # GET /admin/drivers/pending, PUT /admin/documents/{id}
│   │       └── dashboard.py         # GET /dashboard/fleet/stats
│   │
│   ├── schemas/                     # Pydantic v2 Models (Request/Response)
│   │   ├── __init__.py
│   │   ├── auth.py                  # OTPRequest, OTPVerify, TokenResponse, GoogleAuthRequest
│   │   ├── user.py                  # UserRead, DriverRead, DriverUpdate
│   │   ├── order.py                 # OrderCreate, OrderRead, OrderStopCreate, OrderItemCreate
│   │   ├── payment.py               # VietQRRequest, VietQRResponse, PaymentRead
│   │   ├── bid.py                   # BidCreate, BidRead
│   │   ├── tracking.py              # LocationUpdate, TrackingEvent
│   │   ├── eta.py                   # ETAPredictRequest, ETAPredictResponse
│   │   ├── vrp.py                   # VRPOptimizeRequest, VRPOptimizeResponse
│   │   ├── notification.py          # NotificationRead
│   │   └── dashboard.py             # FleetStats, RevenueChart, DriverSummary
│   │
│   ├── models/                      # SQLAlchemy 2.0 ORM Models
│   │   ├── __init__.py
│   │   ├── base.py                  # DeclarativeBase, TimestampMixin
│   │   ├── user.py                  # User
│   │   ├── driver.py                # Driver, DriverDocument
│   │   ├── vehicle.py               # Vehicle
│   │   ├── business.py              # Business, BusinessContract, BusinessDriver
│   │   ├── order.py                 # Order, OrderStop, OrderItem, OrderBid
│   │   ├── payment.py               # Payment
│   │   ├── trip.py                  # ActiveTrip
│   │   ├── tracking.py             # GPSTracking (TimescaleDB hypertable)
│   │   ├── eta.py                   # ETAPrediction
│   │   ├── vrp.py                   # RouteOptimization
│   │   └── notification.py          # Notification, OrderStatusLog
│   │
│   ├── services/                    # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Firebase verify_token, JWT generation
│   │   ├── user_service.py          # Profile CRUD
│   │   ├── order_service.py         # Order creation, validation, status transitions
│   │   ├── pricing_service.py       # Dynamic pricing engine
│   │   ├── payment_service.py       # VietQR generation (NAPAS 247 standard)
│   │   ├── tracking_service.py      # WebSocket manager, location broadcast
│   │   ├── eta_service.py           # XGBoost model inference wrapper
│   │   ├── vrp_service.py           # OR-Tools solver wrapper
│   │   ├── notification_service.py  # FCM push + in-app notification creation
│   │   └── document_service.py      # Document upload, approval workflow
│   │
│   ├── repositories/                # Data Access Layer
│   │   ├── __init__.py
│   │   ├── user_repo.py
│   │   ├── driver_repo.py           # Spatial queries (ST_DWithin)
│   │   ├── order_repo.py
│   │   ├── payment_repo.py
│   │   └── tracking_repo.py
│   │
│   ├── core/                        # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── security.py              # JWT encode/decode, password hashing
│   │   ├── database.py              # AsyncSession, engine, get_db
│   │   ├── redis.py                 # Redis client, pubsub, cache helpers
│   │   ├── firebase.py              # Firebase Admin SDK init
│   │   ├── vietmap.py               # Vietmap API client (routing, geocoding, autocomplete)
│   │   ├── openweather.py           # OpenWeather API client
│   │   └── celery_app.py            # Celery config
│   │
│   └── workers/                     # Celery Task Definitions
│       ├── __init__.py
│       ├── vrp_worker.py            # OR-Tools solve task
│       ├── eta_worker.py            # XGBoost prediction task
│       ├── gps_archiver.py          # Batch insert GPS ticks to TimescaleDB
│       └── notification_worker.py   # FCM dispatch task
│
├── alembic/                         # Database Migrations
│   ├── versions/
│   │   ├── 001_initial_users_and_auth.py
│   │   ├── 002_drivers_vehicles_documents.py
│   │   ├── 003_orders_core_tables.py
│   │   ├── 004_business_contracts_and_fleet.py
│   │   ├── 005_gps_tracking_and_timescaledb.py
│   │   ├── 006_payments_and_vietqr.py
│   │   ├── 007_eta_and_vrp_tables.py
│   │   └── 008_notifications_and_audit_log.py
│   ├── env.py
│   └── alembic.ini
│
├── tests/                           # Pytest
│   ├── conftest.py                  # Fixtures: test DB, async client, mock redis
│   ├── test_auth.py
│   ├── test_orders.py
│   ├── test_pricing.py
│   ├── test_tracking.py
│   ├── test_eta.py
│   ├── test_vrp.py
│   └── test_payments.py
│
├── requirements.txt
├── Dockerfile
├── Dockerfile.dev
└── pyproject.toml
```

---

## 3. CẤU TRÚC THƯ MỤC FRONTEND (Flutter — Simplified Clean Architecture)

```
leopard-frontend/
├── lib/
│   ├── main.dart                        # App entry, MaterialApp, route config
│   ├── app.dart                         # App widget, theme, localization
│   │
│   ├── config/
│   │   ├── app_config.dart              # Base URLs, API keys (loaded from env)
│   │   ├── theme.dart                   # Color scheme, typography
│   │   └── routes.dart                  # Named route definitions
│   │
│   ├── core/
│   │   ├── network/
│   │   │   ├── api_client.dart          # Dio HTTP client with JWT interceptor
│   │   │   ├── websocket_client.dart    # WebSocket connection manager
│   │   │   └── api_exceptions.dart      # Custom exception classes
│   │   ├── utils/
│   │   │   ├── location_utils.dart      # GPS helpers, geohash
│   │   │   ├── map_utils.dart           # Polyline decode, bearing calc
│   │   │   └── validators.dart          # Form validators
│   │   └── widgets/
│   │       ├── loading_overlay.dart
│   │       ├── custom_app_bar.dart
│   │       └── empty_state.dart
│   │
│   ├── features/                        # Feature-first structure
│   │   │
│   │   ├── auth/
│   │   │   ├── data/
│   │   │   │   ├── auth_repository.dart         # Firebase + Backend API
│   │   │   │   └── auth_local_storage.dart      # Secure storage for JWT
│   │   │   ├── domain/
│   │   │   │   └── user_model.dart
│   │   │   └── presentation/
│   │   │       ├── bloc/auth_bloc.dart
│   │   │       ├── bloc/auth_event.dart
│   │   │       ├── bloc/auth_state.dart
│   │   │       ├── pages/login_page.dart
│   │   │       ├── pages/otp_verify_page.dart
│   │   │       └── widgets/phone_input.dart
│   │   │
│   │   ├── booking/
│   │   │   ├── data/
│   │   │   │   ├── booking_repository.dart
│   │   │   │   └── address_autocomplete.dart    # Vietmap Autocomplete
│   │   │   ├── domain/
│   │   │   │   ├── order_model.dart
│   │   │   │   ├── order_stop_model.dart
│   │   │   │   └── vehicle_type_enum.dart
│   │   │   └── presentation/
│   │   │       ├── bloc/booking_bloc.dart
│   │   │       ├── bloc/booking_event.dart
│   │   │       ├── bloc/booking_state.dart
│   │   │       ├── pages/create_order_page.dart
│   │   │       ├── pages/order_confirmation_page.dart
│   │   │       └── widgets/address_input.dart
│   │   │       └── widgets/vehicle_selector.dart
│   │   │
│   │   ├── tracking/
│   │   │   ├── data/
│   │   │   │   └── tracking_repository.dart     # WebSocket listener
│   │   │   ├── domain/
│   │   │   │   └── driver_location_model.dart
│   │   │   └── presentation/
│   │   │       ├── bloc/tracking_bloc.dart
│   │   │       ├── pages/live_tracking_page.dart  # flutter_map + markers
│   │   │       └── widgets/trip_info_card.dart
│   │   │
│   │   ├── payment/
│   │   │   ├── data/
│   │   │   │   └── payment_repository.dart
│   │   │   ├── domain/
│   │   │   │   └── vietqr_model.dart
│   │   │   └── presentation/
│   │   │       ├── bloc/payment_bloc.dart
│   │   │       └── pages/qr_payment_page.dart    # QR display + instructions
│   │   │
│   │   ├── driver/
│   │   │   ├── data/
│   │   │   │   ├── driver_repository.dart
│   │   │   │   └── document_upload_repository.dart
│   │   │   ├── domain/
│   │   │   │   ├── driver_profile_model.dart
│   │   │   │   └── document_model.dart
│   │   │   └── presentation/
│   │   │       ├── bloc/driver_bloc.dart
│   │   │       ├── pages/driver_home_page.dart
│   │   │       ├── pages/navigation_page.dart     # Truck-friendly map
│   │   │       ├── pages/document_upload_page.dart
│   │   │       └── widgets/order_bid_card.dart
│   │   │
│   │   ├── dashboard/                            # Web-only (Enterprise)
│   │   │   ├── data/
│   │   │   │   └── dashboard_repository.dart
│   │   │   ├── domain/
│   │   │   │   └── fleet_stats_model.dart
│   │   │   └── presentation/
│   │   │       ├── bloc/dashboard_bloc.dart
│   │   │       ├── pages/fleet_dashboard_page.dart
│   │   │       └── widgets/revenue_chart.dart
│   │   │
│   │   └── notifications/
│   │       ├── data/
│   │       │   └── notification_repository.dart
│   │       ├── domain/
│   │       │   └── notification_model.dart
│   │       └── presentation/
│   │           ├── bloc/notification_bloc.dart
│   │           └── pages/notifications_page.dart
│   │
│   └── l10n/                            # Localization (nếu cần)
│       └── app_vi.arb
│
├── assets/
│   ├── images/
│   └── fonts/
│
├── test/
│   ├── features/
│   │   ├── auth/auth_bloc_test.dart
│   │   ├── booking/booking_bloc_test.dart
│   │   ├── tracking/tracking_bloc_test.dart
│   │   └── payment/payment_bloc_test.dart
│   └── widget_test.dart
│
├── pubspec.yaml
└── analysis_options.yaml
```

### Quy tắc State Management: Dùng `flutter_bloc` (Cubit cho đơn giản, Bloc cho phức tạp)

| Feature | Pattern | Lý do |
|---|---|---|
| Auth | Cubit | Form đơn giản, ít state transitions |
| Booking | Bloc | Multi-step flow, async API calls nhiều bước |
| Tracking | Bloc | Real-time WebSocket stream, continuous updates |
| Payment | Cubit | QR display + polling đơn giản |
| Driver Nav | Bloc | GPS updates liên tục, route recalculation |

---

## 4. SƠ ĐỒ LUỒNG DỮ LIỆU (Data Flow — Real-time Tracking)

```
Driver Phone                   Backend                         Shipper Phone
────────────                   ───────                         ─────────────
GPS tick (5s)
  │
  ├── WebSocket ──────► FastAPI WS Handler
  │                         │
  │                    ┌────▼────┐
  │                    │  Redis   │  PUBLISH tracking:{order_id}
  │                    │  Pub/Sub │──────┬────────────────────► WebSocket Client
  │                    └────┬────┘      │                            │
  │                         │           │                      ┌─────▼──────┐
  │                    ┌────▼────┐      │                      │ Lerp anim  │
  │                    │Celery   │      │                      │ Update UI  │
  │                    │Batch GPS│      │                      └────────────┘
  │                    │Insert   │      │
  │                    └────┬────┘      │
  │                         │           │
  │                    ┌────▼────┐      │
  │                    │Timescale│      │
  │                    │DB Insert│      │
  │                    └─────────┘      │
  │                                     │
  └── (5s later: next tick) ────────────┘
```

---

## 5. MA TRẬN GIAO TIẾP GIỮA CÁC THÀNH PHẦN (Component Communication)

| From → To | Protocol | Pattern |
|---|---|---|
| Flutter → FastAPI | HTTPS REST | Dio HTTP client + JWT Bearer token |
| Flutter ↔ FastAPI | WSS (WebSocket Secure) | Real-time bidirectional location + events |
| FastAPI → Redis | TCP | Cache get/set, Pub/Sub broadcast |
| FastAPI → PostgreSQL | TCP (asyncpg) | SQLAlchemy 2.0 async queries |
| FastAPI → Celery | Redis broker | Task queue (VRP solve, ETA predict, GPS archive) |
| Celery → PostgreSQL | TCP (psycopg) | Write results, insert GPS batch |
| FastAPI → Firebase | HTTPS | Token verification (firebase-admin SDK) |
| FastAPI → Vietmap | HTTPS REST | Routing, Geocoding, Autocomplete |
| FastAPI → OpenWeather | HTTPS REST | Current weather query |
| Flutter → Firebase | Native SDK | Phone OTP Auth, FCM token registration |
| Firebase → Flutter | FCM | Push notification delivery |

---

## 6. CHIẾN LƯỢC TRIỂN KHAI (Deployment Architecture)

```
┌──────────────────────────────────────────────────────┐
│  VPS Linux (Ubuntu 22.04, 2GB RAM, 2 vCPU)          │
│  Public IP: xxx.xxx.xxx.xxx                          │
│                                                      │
│  ┌────────────────┐  ┌──────────────┐                │
│  │ Docker Compose  │  │ Nginx        │                │
│  │                 │  │ Reverse Proxy│                │
│  │ ┌────────────┐  │  │              │                │
│  │ │ PostgreSQL │  │  │ Port 80 ──►  │                │
│  │ │ :5432      │  │  │ Port 443 ──► │                │
│  │ └────────────┘  │  │              │                │
│  │ ┌────────────┐  │  │ /api/v1/*──► │                │
│  │ │ Redis      │  │  │  FastAPI:8000│                │
│  │ │ :6379      │  │  │              │                │
│  │ └────────────┘  │  │ /ws/* ──────►│                │
│  │ ┌────────────┐  │  │  FastAPI:8000│                │
│  │ │ FastAPI    │  │  │              │                │
│  │ │ :8000      │  │  │ /* (static)─►│                │
│  │ └────────────┘  │  │  Flutter Web │                │
│  │ ┌────────────┐  │  │              │                │
│  │ │ Celery     │  │  └──────────────┘                │
│  │ │ Worker     │  │                                  │
│  │ └────────────┘  │                                  │
│  └────────────────┘                                   │
└──────────────────────────────────────────────────────┘
```

---

## 7. THAM CHIẾU (References)

- ADR-001: Flutter Frontend Technology Selection
- ADR-002: FastAPI Backend Technology Selection
- ADR-003: Vietmap GIS & Routing
- ADR-004: Database Architecture
- ADR-005: AI ETA & VRP Optimization
- SRS: Software Requirements Specification
- ERD: Entity Relationship Diagram
- API Contract: API Documentation
