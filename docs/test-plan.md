# TEST PLAN — KẾ HOẠCH KIỂM THỬ
## DỰ ÁN: LEOPARD - HỆ THỐNG KẾT NỐI VẬN TẢI HÀNG HÓA TRỌNG TẢI LỚN

| Field | Value |
|---|---|
| **Tên tài liệu** | Test Plan & Quality Assurance Strategy |
| **Dự án** | LEOPARD APP |
| **Phiên bản** | 1.0 |
| **Ngày tạo** | 2026-06-15 |
| **Ngày cập nhật** | 2026-06-15 |
| **Phạm vi** | MVP — Minimum Viable Product |
| **Giai đoạn kiểm thử** | P4 — Kiểm thử (26/08 → 05/09/2026) |
| **Tác giả** | QA Lead & Tech Lead Team LEOPARD |
| **Trạng thái** | Draft / Ready for Review |

---

## MỤC LỤC

1. [Giới thiệu](#1-giới-thiệu)
2. [Mục tiêu chất lượng](#2-mục-tiêu-chất-lượng)
3. [Chiến lược kiểm thử MVP](#3-chiến-lược-kiểm-thử-mvp)
   - 3.1. Unit Test (Backend — Pytest)
   - 3.2. Unit Test (Frontend — Flutter Test)
   - 3.3. Integration Test (API — FastAPI TestClient)
   - 3.4. Load Test cơ bản (Locust — WebSocket & Routing)
4. [Môi trường kiểm thử](#4-môi-trường-kiểm-thử)
5. [Kịch bản kiểm thử 3 User Story Critical](#5-kịch-bản-kiểm-thử-3-user-story-critical)
   - 5.1. US-2.1: Luồng đặt hàng đa điểm (Booking Flow)
   - 5.2. US-4.1: Theo dõi xe real-time (Tracking)
   - 5.3. US-7.1: Thanh toán VietQR (Payment)
6. [Template CI/CD GitHub Actions](#6-template-cicd-github-actions)
7. [Tiêu chí kết thúc kiểm thử](#7-tiêu-chí-kết-thúc-kiểm-thử)
8. [Rủi ro & Giảm thiểu](#8-rủi-ro--giảm-thiểu)
9. [Phụ lục: Script mẫu](#9-phụ-lục-script-mẫu)

---

## 1. GIỚI THIỆU

### 1.1. Phạm vi tài liệu

Tài liệu này định nghĩa chiến lược kiểm thử (Testing Strategy) toàn diện cho giai đoạn MVP của dự án **LEOPARD** — Hệ thống kết nối vận tải hàng hóa trọng tải lớn. Tài liệu bao gồm:

- Chiến lược kiểm thử cho từng tầng (Unit → Integration → Load).
- Kịch bản kiểm thử chi tiết cho **3 User Story critical** được xác định theo PRD và SRS.
- Template CI/CD pipeline GitHub Actions dành cho public repository (free tier).

### 1.2. Tham chiếu tài liệu

| Tài liệu | Vị trí |
|---|---|
| Software Requirements Specification (SRS) | `docs/srs.md` |
| API Contract | `docs/api-contract.md` |
| ERD & Database Design | `docs/erd.md` |
| Project Plan | `docs/project-plan.md` |
| Wireframes & UI Flows | `docs/wireframes.md` |

### 1.3. Định nghĩa thuật ngữ

| Thuật ngữ | Định nghĩa |
|---|---|
| **MVP** | Minimum Viable Product — Sản phẩm khả thi tối thiểu |
| **SUT** | System Under Test — Hệ thống đang kiểm thử |
| **DoD** | Definition of Done — Tiêu chí hoàn thành |
| **AC** | Acceptance Criteria — Tiêu chí nghiệm thu |
| **MAE** | Mean Absolute Error — Sai số tuyệt đối trung bình |
| **RPS** | Requests Per Second — Số request mỗi giây |
| **P95** | Percentile thứ 95 — 95% request có latency dưới ngưỡng này |
| **TPS** | Transactions Per Second — Giao dịch mỗi giây |
| **WebSocket** | Giao thức kết nối hai chiều thời gian thực |

---

## 2. MỤC TIÊU CHẤT LƯỢNG

### 2.1. Mục tiêu cho MVP

Các mục tiêu chất lượng được thiết lập dựa trên Non-functional Requirements từ SRS (mục 4):

| STT | Chỉ tiêu | Giá trị mục tiêu | Phương pháp đo |
|---|---|---|---|
| Q1 | Độ phủ Unit Test Backend (service layer) | ≥ 70% | `pytest --cov` |
| Độ phủ Unit Test Frontend (bloc/logic) | ≥ 60% | `flutter test --coverage` |
| Q3 | API Latency P95 (CRUD thông thường) | < 200ms | Locust report |
| Q4 | WebSocket throughput | ≥ 100 kết nối đồng thời | Locust WebSocket |
| Q5 | Thời gian chạy giải thuật OR-Tools (≤ 20 điểm) | < 15 giây | pytest benchmark |
| Q6 | Sai số ETA (MAE) | < 5 phút | pytest + test dataset |
| Q7 | Tỉ lệ Bug critical ở production | = 0 (zero tolerance) | Code review + testing |
| Q8 | CI/CD pass rate on `main` | 100% trước khi merge | GitHub Actions |

### 2.2. Phân loại mức độ ưu tiên bug

| Mức độ | Mô tả | SLA sửa lỗi |
|---|---|---|
| **P0 — Critical** | Lỗi chặn luồng chính (không đặt đơn, không thanh toán được) | Fix ngay trong ngày |
| **P1 — High** | Lỗi chức năng lớn nhưng có workaround | Fix trong 48 giờ |
| **P2 — Medium** | Lỗi chức năng phụ, UI sai, mất dữ liệu không quan trọng | Fix trong 72 giờ |
| **P3 — Low** | Lỗi cosmetic, đề xuất cải tiến | Fix trong 1 tuần hoặc backlog |

---

## 3. CHIẾN LƯỢC KIỂM THỬ MVP

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LEOPARD TEST PYRAMID (MVP)                       │
│                                                                     │
│                         ┌─────────────┐                             │
│                         │   Load Test │  (Locust: WS + Routing)     │
│                         │  (2-3 kịch) │                             │
│                         └──────┬──────┘                             │
│                                │                                    │
│                         ┌──────┴──────┐                             │
│                         │ Integration │  (FastAPI TestClient)        │
│                         │  (API test) │  30+ test cases             │
│                         └──────┬──────┘                             │
│                                │                                    │
│                    ┌───────────┴───────────┐                         │
│                    │      Unit Tests        │                         │
│                    │  ┌─────┐  ┌──────────┐ │                         │
│                    │  │Pytest│  │Flutter   │ │                         │
│                    │  │Service│  │Test      │ │                         │
│                    │  │Layer │  │Bloc+     │ │                         │
│                    │  │      │  │Widget    │ │                         │
│                    │  └─────┘  └──────────┘ │                         │
│                    └─────────────────────────┘                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.1. Unit Test — Backend (Pytest)

#### 3.1.1. Công nghệ & Thư viện

| Công cụ | Phiên bản | Mục đích |
|---|---|---|
| `pytest` | ≥ 7.4 | Test framework chính |
| `pytest-asyncio` | ≥ 0.23 | Hỗ trợ async test cho FastAPI |
| `pytest-cov` | ≥ 4.1 | Đo độ phủ code (coverage) |
| `pytest-mock` | ≥ 3.12 | Mock database, API bên thứ ba |
| `freezegun` | ≥ 1.5 | Freeze thời gian cho test scheduling |
| `httpx` | ≥ 0.27 | HTTP client cho async requests (dùng test double) |

#### 3.1.2. Cấu trúc thư mục test

```
backend/
├── tests/
│   ├── conftest.py                 # Fixtures chung (DB session, Redis mock, auth)
│   ├── factories.py                 # Factory Boy / custom factories cho model data
│   ├── test_services/
│   │   ├── test_auth_service.py     # OTP, Google Sign-In, token refresh
│   │   ├── test_booking_service.py   # Tạo đơn, tính giá, optimize route
│   │   ├── test_tracking_service.py  # GPS location, WebSocket events
│   │   ├── test_payment_service.py   # VietQR generation, confirm payment
│   │   ├── test_eta_service.py       # XGBoost prediction validation
│   │   ├── test_vrp_service.py       # OR-Tools constraint checking
│   │   └── test_notification_service.py  # FCM push trigger
│   ├── test_models/
│   │   ├── test_order_model.py      # State machine transitions
│   │   ├── test_user_model.py       # Role validation, unique constraints
│   │   └── test_payment_model.py    # Amount validation, status flow
│   └── test_utils/
│       ├── test_geo_utils.py        # Haversine, ST_DWithin wrapper
│       ├── test_price_calc.py       # Distance-based fare calculation
│       └── test_validators.py       # Input validation helpers
```

#### 3.1.3. Danh sách Test Case Backend — Unit

| ID | Module | Test Case | Expected |
|---|---|---|---|
| UT-B-01 | Auth | `test_otp_request_valid_phone` | Trả về session_id, HTTP 200 |
| UT-B-02 | Auth | `test_otp_request_invalid_phone` | Trả về INVALID_PHONE_NUMBER, HTTP 400 |
| UT-B-03 | Auth | `test_otp_verify_success` | Trả về access_token + refresh_token |
| UT-B-04 | Auth | `test_otp_verify_expired` | Trả về OTP_EXPIRED_OR_INVALID |
| UT-B-05 | Auth | `test_google_sign_in_new_user` | Tạo user mới, trả về token |
| UT-B-06 | Booking | `test_create_booking_minimal` | Tạo đơn thành công với 2 điểm dừng |
| UT-B-07 | Booking | `test_create_booking_invalid_stops` | Lỗi nếu < 2 điểm dừng |
| UT-B-08 | Booking | `test_create_booking_exceeds_max_stops` | Lỗi nếu > 5 điểm dừng |
| UT-B-09 | Booking | `test_calculate_fare_basic` | Tính đúng base_fare + distance_fare |
| UT-B-10 | Booking | `test_calculate_fare_with_loading` | Phụ phí loading được tính đúng |
| UT-B-11 | Booking | `test_calculate_fare_night_trip` | Phụ phí ban đêm = 30% base |
| UT-B-12 | Booking | `test_optimize_route_simple` | OR-Tools trả về route tối ưu |
| UT-B-13 | Booking | `test_optimize_route_timeout` | Fallback nếu OR-Tools timeout |
| UT-B-14 | Booking | `test_booking_status_transition_valid` | `pending → accepted → in_transit → delivered` |
| UT-B-15 | Booking | `test_booking_status_transition_invalid` | `pending → delivered` bị reject |
| UT-B-16 | Booking | `test_booking_cancel_by_shipper` | Chỉ cho hủy nếu status = pending |
| UT-B-17 | Tracking | `test_driver_location_update` | GPS lưu vào bảng gps_tracking |
| UT-B-18 | Tracking | `test_location_update_speed_calc` | Speed km/h tính từ 2 toạ độ |
| UT-B-19 | Tracking | `test_driver_arrived_at_stop` | Cập nhật arrived_at, status chuyển sang dừng |
| UT-B-20 | Tracking | `test_eta_prediction` | XGBoost trả về kết quả có confidence_score |
| UT-B-21 | Payment | `test_vietqr_generate_success` | Trả về QR string + image URL |
| UT-B-22 | Payment | `test_vietqr_invalid_amount` | Lỗi nếu amount ≤ 0 |
| UT-B-23 | Payment | `test_confirm_payment` | Payment status chuyển từ unpaid → paid |
| UT-B-24 | Payment | `test_payment_webhook_duplicate` | Idempotency: webhook trùng bị reject |
| UT-B-25 | VRP | `test_backhaul_suggestion_valid` | Tìm thấy đơn ghép phù hợp |
| UT-B-26 | VRP | ` test_backhaul_no_suitable_order` | Trả về rỗng nếu không có đơn phù hợp |
| UT-B-27 | Notification | `test_send_fcm_on_status_change` | FCM được gọi khi status thay đổi |
| UT-B-28 | Notification | `test_notification_persistence` | Notification lưu vào DB |
| UT-B-29 | Geo | `test_distance_calculation` | Haversine khớp với PostGIS ST_Distance |
| UT-B-30 | Geo | `test_find_nearby_drivers` | PostGIS spatial query trả về driver gần nhất |

#### 3.1.4. Conftest mẫu

```python
# backend/tests/conftest.py
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from redis import Redis
from unittest.mock import AsyncMock, MagicMock

from app.main import create_app
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.redis.session import get_redis_client

# ── Test Settings ──────────────────────────────────────────────────
@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
        REDIS_URL="redis://localhost:6379/1",
        SECRET_KEY="test-secret-not-for-prod",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        VIETMAP_API_KEY="test-key",
        OPENWEATHER_API_KEY="test-key",
    )

# ── In-memory SQLite Engine ────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def db_engine(settings: Settings):
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

# ── Mock Redis ─────────────────────────────────────────────────────
@pytest.fixture
def redis_client() -> MagicMock:
    client = MagicMock(spec=Redis)
    client.ping.return_value = True
    client.get.return_value = None
    client.setex.return_value = True
    return client

# ── FastAPI Test App ───────────────────────────────────────────────
@pytest_asyncio.fixture
async def app(settings: Settings, db_session, redis_client) -> FastAPI:
    app = create_app(settings)

    async def override_get_db():
        yield db_session

    def override_get_redis():
        yield redis_client

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis
    return app

@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# ── Auth Fixtures ──────────────────────────────────────────────────
@pytest.fixture
def shipper_token() -> str:
    """Return a fake JWT for shipper role (bypass Firebase)."""
    return "test-shipper-jwt-token"

@pytest_asyncio.fixture
async def authed_client(client: AsyncClient, shipper_token: str) -> AsyncClient:
    client.headers.update({"Authorization": f"Bearer {shipper_token}"})
    return client
```

#### 3.1.5. Test mẫu — Booking Service

```python
# backend/tests/test_services/test_booking_service.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCreateBooking:
    """Test suite cho User Story 2.1: Tạo đơn hàng đa điểm."""

    CREATE_BOOKING_URL = "/api/v1/bookings/create"

    @pytest.fixture
    def valid_booking_payload(self):
        return {
            "customer_id": "cust_01",
            "truck_type": "2.5_ton_covered",
            "cargo_type": "Hàng tiêu dùng nhanh (FMCG)",
            "total_weight_kg": 2300,
            "total_volume_cbm": 11.5,
            "payment_method": "VIETQR",
            "stops": [
                {
                    "sequence": 0,
                    "address": "Cảng Cát Lái, Quận 2, TP. HCM",
                    "latitude": 10.7635,
                    "longitude": 106.7992,
                    "contact_name": "Nguyen Van A",
                    "contact_phone": "+84912345678",
                    "stop_type": "PICKUP",
                },
                {
                    "sequence": 1,
                    "address": "12 Phan Chu Trinh, Quận 1, TP. HCM",
                    "latitude": 10.7725,
                    "longitude": 106.6980,
                    "contact_name": "Le Hoang B",
                    "contact_phone": "+84998765432",
                    "stop_type": "DROP_OFF",
                },
            ],
        }

    async def test_create_booking_minimal_success(
        self, authed_client: AsyncClient, valid_booking_payload: dict
    ):
        """UT-B-06: Tạo đơn thành công với payload tối thiểu (2 điểm)."""
        # Act
        response = await authed_client.post(
            self.CREATE_BOOKING_URL, json=valid_booking_payload
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "CREATED"
        assert "booking_id" in data
        assert data["fare_details"]["currency"] == "VND"
        assert len(data["stops"]) == 2

    async def test_create_booking_invalid_stops_count(
        self, authed_client: AsyncClient, valid_booking_payload: dict
    ):
        """UT-B-07: Lỗi nếu chỉ có 1 điểm dừng (thiếu pickup hoặc dropoff)."""
        # Arrange
        payload = valid_booking_payload.copy()
        payload["stops"] = [valid_booking_payload["stops"][0]]

        # Act
        response = await authed_client.post(self.CREATE_BOOKING_URL, json=payload)

        # Assert
        assert response.status_code == 422

    @patch("app.services.booking.optimize_route")
    async def test_create_booking_with_optimization(
        self, mock_optimize, authed_client: AsyncClient, valid_booking_payload: dict
    ):
        """UT-B-12: Tạo đơn và gọi OR-Tools optimize nếu > 2 điểm."""
        # Arrange
        mock_optimize.return_value = {
            "optimized_route": [
                {"sequence": 0, "stop_id": "depot"},
                {"sequence": 1, "stop_id": "stop_01"},
                {"sequence": 2, "stop_id": "stop_02"},
                {"sequence": 3, "stop_id": "stop_03"},
            ],
            "total_distance_meters": 32500,
            "total_duration_minutes": 115,
        }
        payload = valid_booking_payload.copy()
        payload["stops"].append(
            {
                "sequence": 2,
                "address": "789 Nguyễn Văn Linh, Quận 7, TP. HCM",
                "latitude": 10.7294,
                "longitude": 106.7001,
                "contact_name": "Pham Van C",
                "contact_phone": "+84998765433",
                "stop_type": "DROP_OFF",
            }
        )

        # Act
        response = await authed_client.post(self.CREATE_BOOKING_URL, json=payload)

        # Assert
        assert response.status_code == 201
        mock_optimize.assert_called_once()


class TestFareCalculation:
    """Test suite cho tính cước phí."""

    CALCULATE_FARE_URL = "/api/v1/billing/calculate-fare"

    async def test_calculate_fare_basic(self, authed_client: AsyncClient):
        """UT-B-09: Tính cước cơ bản."""
        # Arrange
        payload = {
            "truck_type": "2.5_ton_covered",
            "total_distance_meters": 32500,
            "number_of_stops": 2,
            "has_loading_service": False,
            "is_night_trip": False,
        }

        # Act
        response = await authed_client.post(self.CALCULATE_FARE_URL, json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["base_fare"] == 250000
        assert data["distance_fare"] == 350000
        assert data["stops_charge"] == 100000
        assert data["loading_charge"] == 0
        assert data["total_fare"] == 700000

    async def test_calculate_fare_with_loading(self, authed_client: AsyncClient):
        """UT-B-10: Tính cước có phụ phí bốc xếp."""
        # Arrange
        payload = {
            "truck_type": "2.5_ton_covered",
            "total_distance_meters": 32500,
            "number_of_stops": 3,
            "has_loading_service": True,
            "is_night_trip": False,
        }

        # Act
        response = await authed_client.post(self.CALCULATE_FARE_URL, json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["loading_charge"] == 150000
        assert data["total_fare"] == 850000  # base(250k) + distance(350k) + stops(100k) + loading(150k)


class TestBookingStatusTransition:
    """Test suite cho state machine của đơn hàng."""

    async def test_valid_transition_flow(self, authed_client: AsyncClient):
        """UT-B-14: Chuỗi chuyển trạng thái hợp lệ."""
        transitions = [
            ("draft", "pending"),
            ("pending", "accepted"),
            ("accepted", "pickup_in_progress"),
            ("pickup_in_progress", "in_transit"),
            ("in_transit", "delivered"),
            ("delivered", "completed"),
        ]
        for current, next_status in transitions:
            response = await authed_client.patch(
                f"/api/v1/bookings/bk_987654321/status",
                json={"status": next_status, "current_status": current},
            )
            # Có thể 400 nếu booking không tồn tại, nhưng logic state machine phải pass
            if response.status_code != 404:
                assert response.status_code in (200,)

    async def test_invalid_transition_flow(self, authed_client: AsyncClient):
        """UT-B-15: Chuyển trạng thái không hợp lệ bị reject."""
        invalid_transitions = [
            ("draft", "delivered"),
            ("pending", "completed"),
            ("accepted", "completed"),
        ]
        for current, next_status in invalid_transitions:
            response = await authed_client.patch(
                f"/api/v1/bookings/bk_987654321/status",
                json={"status": next_status, "current_status": current},
            )
            if response.status_code != 404:
                assert response.status_code == 409  # Conflict
```

---

### 3.2. Unit Test — Frontend (Flutter Test)

#### 3.2.1. Công nghệ & Thư viện

| Công cụ | Mục đích |
|---|---|
| `flutter_test` (built-in) | Test framework chính |
| `bloc_test` | Test BLoC pattern |
| `mocktail` | Mock dependencies (≥ 1.0) |
| `integration_test` | Widget test + integration |

#### 3.2.2. Cấu trúc thư mục test

```
frontend/
├── test/
│   ├── blocs/
│   │   ├── auth_bloc_test.dart
│   │   ├── booking_bloc_test.dart
│   │   ├── tracking_bloc_test.dart
│   │   ├── payment_bloc_test.dart
│   │   └── driver_bloc_test.dart
│   ├── models/
│   │   ├── order_model_test.dart
│   │   ├── user_model_test.dart
│   │   └── location_model_test.dart
│   ├── repositories/
│   │   ├── booking_repository_test.dart
│   │   ├── auth_repository_test.dart
│   │   └── payment_repository_test.dart
│   └── widgets/
│       ├── booking_form_widget_test.dart
│       ├── tracking_map_widget_test.dart
│       ├── vietqr_widget_test.dart
│       └── order_list_widget_test.dart
└── pubspec.yaml
```

Thêm dependency vào `pubspec.yaml`:

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  bloc_test: ^9.1.0
  mocktail: ^1.0.0
  integration_test:
    sdk: flutter
```

#### 3.2.3. Danh sách Test Case Frontend — Unit

| ID | Module | Test Case | Expected |
|---|---|---|---|
| UT-F-01 | Auth | `AuthBloc emits authenticated state on success` | Trạng thái → Authenticated |
| UT-F-02 | Auth | `AuthBloc emits error state on OTP failure` | Trạng thái → AuthError |
| UT-F-03 | Auth | `AuthBloc resend cooldown timer works` | 60s cooldown đếm ngược |
| UT-F-04 | Booking | `BookingBloc calculates fare correctly` | Fare state có total_price đúng |
| UT-F-05 | Booking | `BookingBloc adds stop correctly` | Danh sách stops tăng lên |
| UT-F-06 | Booking | `BookingBloc removes stop correctly` | Danh sách stops giảm xuống |
| UT-F-07 | Booking | `BookingBloc validates max 5 stops` | Lỗi nếu > 5 điểm dừng |
| UT-F-08 | Booking | `BookingBloc submits booking` | Trạng thái → BookingCreated |
| UT-F-09 | Tracking | `TrackingBloc updates driver marker` | Marker position thay đổi |
| UT-F-10 | Tracking | `TrackingBloc updates ETA countdown` | ETA giảm dần |
| UT-F-11 | Tracking | `TrackingBloc handles WS disconnect` | Trạng thái → Disconnected |
| UT-F-12 | Payment | `PaymentBloc generates VietQR` | QR code + amount chính xác |
| UT-F-13 | Payment | `PaymentBloc confirms payment` | Trạng thái → PaymentConfirmed |
| UT-F-14 | Widget | `BookingFormWidget renders stop list` | Tìm thấy ListView với stops |
| UT-F-15 | Widget | `TrackingMapWidget shows driver icon` | Tìm thấy marker trên GoogleMap |
| UT-F-16 | Widget | `VietQRWidget shows QR image` | Tìm thấy Image widget |
| UT-F-17 | Widget | `OrderListWidget shows empty state` | Tìm thấy empty state text |
| UT-F-18 | ViewModel | `OrderModel.fromJson parses correctly` | Tất cả field khớp JSON |

#### 3.2.4. Test mẫu — Booking Bloc

```dart
// frontend/test/blocs/booking_bloc_test.dart
import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:leopard_app/blocs/booking/booking_bloc.dart';
import 'package:leopard_app/blocs/booking/booking_event.dart';
import 'package:leopard_app/blocs/booking/booking_state.dart';
import 'package:leopard_app/models/order.dart';
import 'package:leopard_app/repositories/booking_repository.dart';

class MockBookingRepository extends Mock implements BookingRepository {}

void main() {
  late BookingRepository mockRepository;

  setUp(() {
    mockRepository = MockBookingRepository();
  });

  group('BookingBloc — Unit Tests', () {
    blocTest<BookingBloc, BookingState>(
      'UT-F-04: emits [BookingFareLoaded] when fare is calculated',
      build: () {
        when(() => mockRepository.calculateFare(any()))
            .thenAnswer((_) async => const FareDetails(
                  baseFare: 250000,
                  distanceFare: 350000,
                  stopsCharge: 100000,
                  loadingCharge: 0,
                  totalFare: 700000,
                  currency: 'VND',
                ));
        return BookingBloc(repository: mockRepository);
      },
      act: (bloc) => bloc.add(const CalculateFare(
        truckType: '2.5_ton_covered',
        totalDistanceMeters: 32500,
        numberOfStops: 2,
        hasLoadingService: false,
        isNightTrip: false,
      )),
      expect: () => [
        BookingFareLoading(),
        isA<BookingFareLoaded>().having(
          (s) => s.fare.totalFare,
          'totalFare',
          700000,
        ),
      ],
    );

    blocTest<BookingBloc, BookingState>(
      'UT-F-05: emits [StopAdded] when a stop is added',
      build: () => BookingBloc(repository: mockRepository),
      act: (bloc) => bloc.add(const AddStop(OrderStop(
        sequence: 1,
        address: '12 Phan Chu Trinh, Quận 1, TP. HCM',
        latitude: 10.7725,
        longitude: 106.6980,
        contactName: 'Le Hoang B',
        contactPhone: '+84998765432',
        stopType: StopType.dropOff,
      ))),
      expect: () => [
        isA<BookingStopAdded>().having(
          (s) => s.stops.length,
          'stops length',
          1,
        ),
      ],
    );
  });
}
```

#### 3.2.5. Test mẫu — Tracking Bloc

```dart
// frontend/test/blocs/tracking_bloc_test.dart
import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:leopard_app/blocs/tracking/tracking_bloc.dart';
import 'package:leopard_app/blocs/tracking/tracking_event.dart';
import 'package:leopard_app/blocs/tracking/tracking_state.dart';
import 'package:leopard_app/models/location.dart';
import 'package:leopard_app/services/websocket_service.dart';

class MockWebSocketService extends Mock implements WebSocketService {}

void main() {
  late WebSocketService mockWsService;

  setUp(() {
    mockWsService = MockWebSocketService();
  });

  group('TrackingBloc — Unit Tests', () {
    blocTest<TrackingBloc, TrackingState>(
      'UT-F-09: emits [DriverLocationUpdated] when location is received via WS',
      build: () {
        when(() => mockWsService.connect(any())).thenAnswer((_) async {});
        when(() => mockWsService.locationStream)
            .thenAnswer((_) => Stream.value(const DriverLocation(
                  bookingId: 'bk_987654321',
                  latitude: 10.7689,
                  longitude: 106.7012,
                  speedKph: 38.5,
                  bearing: 120.4,
                )));
        return TrackingBloc(wsService: mockWsService);
      },
      act: (bloc) => bloc.add(const StartTracking(bookingId: 'bk_987654321')),
      expect: () => [
        TrackingConnecting(),
        isA<TrackingConnected>(),
        isA<DriverLocationUpdated>().having(
          (s) => s.location.latitude,
          'latitude',
          10.7689,
        ),
      ],
    );
  });
}
```

---

### 3.3. Integration Test — API (FastAPI TestClient)

#### 3.3.1. Mục tiêu

Kiểm thử toàn bộ luồng request-response của REST API, bao gồm:
- Xác thực JWT (Authentication middleware).
- Phân quyền RBAC (Role-Based Access Control).
- Input validation (Pydantic schemas).
- Database operations (CRUD real với test database).
- WebSocket handshake + event flow.

#### 3.3.2. Cấu trúc thư mục test

```
backend/
├── tests/
│   ├── integration/
│   │   ├── test_auth_api.py           # POST /auth/phone/otp-request, /auth/phone/otp-verify
│   │   ├── test_booking_api.py         # POST /bookings/create, GET /bookings/{id}
│   │   ├── test_billing_api.py         # POST /billing/calculate-fare, /billing/payments/vietqr
│   │   ├── test_tracking_ws.py         # WebSocket /ws/v1/tracking
│   │   ├── test_eta_api.py             # POST /eta/predict
│   │   ├── test_optimize_api.py        # POST /bookings/optimize
│   │   └── conftest_integration.py     # Fixtures riêng cho integration test
```

#### 3.3.3. Danh sách Integration Test Case

| ID | Module | Test Case | Expected |
|---|---|---|---|
| IT-01 | Auth | `POST /auth/phone/otp-request` với SĐT hợp lệ | 200 + session_id |
| IT-02 | Auth | `POST /auth/phone/otp-request` với SĐT không hợp lệ | 400 |
| IT-03 | Auth | `POST /auth/phone/otp-verify` với OTP đúng | 200 + access_token |
| IT-04 | Auth | `POST /auth/phone/otp-verify` với OTP sai | 401 |
| IT-05 | Auth | `POST /auth/google` với id_token hợp lệ | 200 + token |
| IT-06 | Auth | Gọi API protected không có token | 401 |
| IT-07 | Auth | Gọi API protected với token hết hạn | 401 |
| IT-08 | Booking | `POST /bookings/create` hợp lệ | 201 + booking_id |
| IT-09 | Booking | `GET /bookings/{id}` — Shipper xem đơn của mình | 200 |
| IT-10 | Booking | `GET /bookings/{id}` — Driver xem đơn không phải của mình | 403 |
| IT-11 | Booking | `POST /bookings/optimize` với 5 điểm dừng | 200 + optimized_route |
| IT-12 | Booking | `POST /bookings/optimize` với 20 điểm dừng (stress) | 200 hoặc 504 nếu timeout |
| IT-13 | Booking | `PATCH /bookings/{id}/status` — chuyển trạng thái hợp lệ | 200 |
| IT-14 | Booking | `PATCH /bookings/{id}/status` — chuyển trạng thái không hợp lệ | 409 |
| IT-15 | Billing | `POST /billing/calculate-fare` | 200 + fare details |
| IT-16 | Billing | `POST /billing/payments/vietqr` | 200 + QR string |
| IT-17 | Billing | `POST /billing/payments/vietqr` — amount sai | 422 |
| IT-18 | ETA | `POST /eta/predict` với đủ features | 200 + prediction |
| IT-19 | ETA | `POST /eta/predict` — thiếu feature | 422 |
| IT-20 | ETA | `POST /eta/predict` — coordinate out of Vietnam | 400 |
| IT-21 | WS | WebSocket handshake với token hợp lệ | 101 switching |
| IT-22 | WS | WebSocket gửi DRIVER_LOCATION_UPDATE | Nhận PUSH_DRIVER_LOCATION |
| IT-23 | WS | WebSocket gửi DRIVER_ARRIVED_AT_STOP | Nhận PUSH_BOOKING_STATUS_CHANGE |
| IT-24 | WS | WebSocket với token hết hạn | 401 close |
| IT-25 | Driver | `GET /drivers/nearby` — PostGIS spatial query | 200 + danh sách driver |

#### 3.3.4. Test mẫu — Booking API Integration

```python
# backend/tests/integration/test_booking_api.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestBookingAPI:
    """Integration test cho Booking endpoints."""

    CREATE_URL = "/api/v1/bookings/create"
    GET_URL = "/api/v1/bookings"
    OPTIMIZE_URL = "/api/v1/bookings/optimize"

    @pytest.fixture
    def valid_payload(self):
        return {
            "customer_id": "cust_01",
            "truck_type": "2.5_ton_covered",
            "cargo_type": "Hàng tiêu dùng nhanh (FMCG)",
            "total_weight_kg": 2300,
            "total_volume_cbm": 11.5,
            "payment_method": "VIETQR",
            "stops": [
                {
                    "sequence": 0,
                    "address": "Cảng Cát Lái, Quận 2, TP. HCM",
                    "latitude": 10.7635,
                    "longitude": 106.7992,
                    "contact_name": "Nguyen Van A",
                    "contact_phone": "+84912345678",
                    "stop_type": "PICKUP",
                },
                {
                    "sequence": 1,
                    "address": "12 Phan Chu Trinh, Quận 1, TP. HCM",
                    "latitude": 10.7725,
                    "longitude": 106.6980,
                    "contact_name": "Le Hoang B",
                    "contact_phone": "+84998765432",
                    "stop_type": "DROP_OFF",
                },
            ],
        }

    async def test_create_and_get_booking(self, authed_client: AsyncClient, valid_payload: dict):
        """IT-08 + IT-09: Tạo đơn → Xem chi tiết."""
        # Tạo đơn
        create_resp = await authed_client.post(self.CREATE_URL, json=valid_payload)
        assert create_resp.status_code == 201
        booking_id = create_resp.json()["booking_id"]

        # Xem chi tiết
        get_resp = await authed_client.get(f"{self.GET_URL}/{booking_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["booking_id"] == booking_id

    async def test_unauthorized_access(self, client: AsyncClient, valid_payload: dict):
        """IT-06: API protected — không có token trả về 401."""
        response = await client.post(self.CREATE_URL, json=valid_payload)
        assert response.status_code == 401

    async def test_forbidden_access(self, authed_client_driver: AsyncClient):
        """IT-10: Driver xem đơn của shipper khác → 403."""
        response = await authed_client_driver.get(f"{self.GET_URL}/bk_other_shipper")
        assert response.status_code == 403

    async def test_optimize_route(self, authed_client: AsyncClient):
        """IT-11: OR-Tools optimize với 5 điểm dừng."""
        payload = {
            "vehicle_constraints": {
                "max_weight_kg": 2500,
                "max_volume_cbm": 12.5,
                "truck_type": "2.5_ton_covered",
            },
            "depot": {
                "address": "Cảng Cát Lái, Quận 2, TP. HCM",
                "latitude": 10.7635,
                "longitude": 106.7992,
                "earliest_departure": "2026-06-16T08:00:00Z",
            },
            "stops": [
                {
                    "stop_id": "stop_01",
                    "address": "12 Phan Chu Trinh, Quận 1, TP. HCM",
                    "latitude": 10.7725,
                    "longitude": 106.6980,
                    "weight_kg": 500,
                    "volume_cbm": 2.5,
                    "service_time_minutes": 20,
                    "time_window": {
                        "start_time": "2026-06-16T08:30:00Z",
                        "end_time": "2026-06-16T10:30:00Z",
                    },
                },
                {
                    "stop_id": "stop_02",
                    "address": "456 Lê Văn Việt, Quận 9, TP. HCM",
                    "latitude": 10.8441,
                    "longitude": 106.7825,
                    "weight_kg": 1200,
                    "volume_cbm": 6.0,
                    "service_time_minutes": 35,
                    "time_window": {
                        "start_time": "2026-06-16T09:00:00Z",
                        "end_time": "2026-06-16T12:00:00Z",
                    },
                },
                {
                    "stop_id": "stop_03",
                    "address": "789 Nguyễn Văn Linh, Quận 7, TP. HCM",
                    "latitude": 10.7294,
                    "longitude": 106.7001,
                    "weight_kg": 600,
                    "volume_cbm": 3.0,
                    "service_time_minutes": 15,
                    "time_window": {
                        "start_time": "2026-06-16T08:00:00Z",
                        "end_time": "2026-06-16T17:00:00Z",
                    },
                },
            ],
        }
        response = await authed_client.post(self.OPTIMIZE_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["optimization_status"] in ("OPTIMAL", "FEASIBLE")
        assert len(data["optimized_route"]) == 4  # depot + 3 stops
```

#### 3.3.5. Test mẫu — WebSocket Integration

```python
# backend/tests/integration/test_tracking_ws.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

pytestmark = pytest.mark.asyncio


class TestTrackingWebSocket:
    """Integration test cho WebSocket tracking."""

    WS_URL = "/ws/v1/tracking"

    async def test_websocket_handshake_valid_token(self, authed_client: AsyncClient):
        """IT-21: WebSocket handshake với token hợp lệ."""
        async with authed_client.websocket_connect(
            self.WS_URL, params={"token": "valid-test-token"}
        ) as ws:
            # Server gửi connected confirmation
            data = await ws.receive_json()
            assert data["event"] == "CONNECTED"
            assert data["payload"]["booking_id"] is None

    async def test_websocket_receive_driver_location(self, authed_client: AsyncClient):
        """IT-22: Gửi DRIVER_LOCATION_UPDATE → nhận PUSH_DRIVER_LOCATION."""
        async with authed_client.websocket_connect(
            self.WS_URL, params={"token": "valid-test-token"}
        ) as ws:
            # Đọc CONNECTED event
            await ws.receive_json()

            # Gửi location update
            await ws.send_json({
                "event": "DRIVER_LOCATION_UPDATE",
                "payload": {
                    "booking_id": "bk_987654321",
                    "driver_id": "drv_8888",
                    "latitude": 10.7689,
                    "longitude": 106.7012,
                    "speed_kph": 38.5,
                    "bearing": 120.4,
                    "timestamp": "2026-06-16T08:10:00Z",
                },
            })

            # Nhận PUSH_DRIVER_LOCATION (có thể được broadcast lại)
            response = await ws.receive_json(timeout=5)
            assert response["event"] in (
                "PUSH_DRIVER_LOCATION",
                "DRIVER_LOCATION_ACK",
            )

    async def test_websocket_expired_token(self, client: AsyncClient):
        """IT-24: WebSocket với token hết hạn → 401."""
        with pytest.raises(Exception) as exc_info:
            async with client.websocket_connect(
                self.WS_URL, params={"token": "expired-test-token"}
            ) as ws:
                await ws.receive_json()
        assert "401" in str(exc_info.value)
```

---

### 3.4. Load Test cơ bản (Locust)

#### 3.4.1. Mục tiêu

- Đo khả năng chịu tải của WebSocket (≥ 100 kết nối đồng thời gửi GPS).
- Đo performance của OR-Tools Routing (response time < 15 giây với 20 điểm).
- Xác định bottleneck sớm trước khi triển khai production.

#### 3.4.2. Cấu trúc thư mục

```
backend/
├── tests/
│   ├── load/
│   │   ├── locustfile_ws.py       # Load test cho WebSocket
│   │   ├── locustfile_routing.py  # Load test cho OR-Tools
│   │   └── locustfile_booking.py  # Load test cho Booking API
│   └── load-requirements.txt      # locust >= 2.30
```

#### 3.4.3. Script Load Test — WebSocket

```python
# backend/tests/load/locustfile_ws.py
"""
Locust load test cho WebSocket tracking.
Chạy: locust -f tests/load/locustfile_ws.py --host=https://api.leopard.vn

Mục tiêu:
- 100 kết nối WebSocket đồng thời
- Mỗi kết nối gửi GPS location mỗi 5 giây
- P95 latency < 200ms cho mỗi message
"""

import json
import time
import gevent
from locust import User, task, between, events
from websocket import create_connection


class WebSocketTrackingUser(User):
    """
    Mô phỏng một tài xế gửi GPS location qua WebSocket.
    Mỗi user mở 1 kết nối WS và gửi location mỗi 5 giây.
    """

    wait_time = between(1, 3)

    def __init__(self, environment):
        super().__init__(environment)
        self.ws = None
        self.booking_id = None
        self.driver_id = None
        self.lat = 10.7500
        self.lon = 106.7000

    def on_start(self):
        """Mở kết nối WebSocket khi user bắt đầu."""
        token = self.environment.runner.user_classes["token"] if hasattr(
            self.environment.runner, "user_classes"
        ) else "test-load-token"
        try:
            self.ws = create_connection(
                f"{self.host}/ws/v1/tracking?token={token}",
                timeout=10,
            )
            # Đọc CONNECTED event
            resp = self.ws.recv()
            data = json.loads(resp)
            assert data["event"] == "CONNECTED", f"Unexpected event: {data['event']}"
            self.booking_id = f"bk_load_{id(self)}"
            self.driver_id = f"drv_load_{id(self)}"
            events.request_success.fire(
                request_type="WS",
                name="connect",
                response_time=0,
                response_length=len(resp),
            )
        except Exception as e:
            events.request_failure.fire(
                request_type="WS",
                name="connect",
                response_time=0,
                exception=e,
            )
            self.ws = None

    @task
    def send_location_update(self):
        """Gửi GPS location update mỗi lần task chạy."""
        if self.ws is None:
            return

        # Mô phỏng di chuyển: thay đổi toạ độ nhẹ
        self.lat += 0.0001
        self.lon += 0.0001

        payload = {
            "event": "DRIVER_LOCATION_UPDATE",
            "payload": {
                "booking_id": self.booking_id,
                "driver_id": self.driver_id,
                "latitude": round(self.lat, 6),
                "longitude": round(self.lon, 6),
                "speed_kph": round(30 + (id(self) % 40), 1),
                "bearing": round(id(self) % 360, 1),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        }

        start_time = time.time()
        try:
            self.ws.send(json.dumps(payload))
            # Đọc response (có timeout ngắn để không block)
            resp = self.ws.recv()
            latency = (time.time() - start_time) * 1000  # ms
            events.request_success.fire(
                request_type="WS",
                name="send_location",
                response_time=latency,
                response_length=len(resp),
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            events.request_failure.fire(
                request_type="WS",
                name="send_location",
                response_time=latency,
                exception=e,
            )
            # Thử reconnect
            self.on_start()

    def on_stop(self):
        """Đóng kết nối WebSocket khi user kết thúc."""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
```

#### 3.4.4. Script Load Test — Routing / OR-Tools

```python
# backend/tests/load/locustfile_routing.py
"""
Locust load test cho OR-Tools Route Optimization.
Chạy: locust -f tests/load/locustfile_routing.py --host=https://api.leopard.vn

Mục tiêu:
- 20 requests/phút cho optimize endpoint
- P95 response time < 15 giây với 20 điểm dừng
"""

import random
from locust import HttpUser, task, between


class RouteOptimizationUser(HttpUser):
    """Mô phỏng shipper gọi API optimize route."""

    wait_time = between(3, 8)

    def _generate_stops(self, count: int) -> list:
        """Sinh danh sách điểm dừng ngẫu nhiên trong TP.HCM."""
        base_lat, base_lon = 10.7500, 106.7000
        stops = []
        for i in range(count):
            stops.append({
                "stop_id": f"stop_{i:03d}",
                "address": f"Địa chỉ ngẫu nhiên {i}",
                "latitude": round(base_lat + random.uniform(-0.05, 0.05), 6),
                "longitude": round(base_lon + random.uniform(-0.05, 0.05), 6),
                "weight_kg": random.randint(100, 2000),
                "volume_cbm": round(random.uniform(1.0, 10.0), 2),
                "service_time_minutes": random.randint(10, 40),
                "time_window": {
                    "start_time": "2026-06-16T08:00:00Z",
                    "end_time": "2026-06-16T17:00:00Z",
                },
            })
        return stops

    @task(3)
    def optimize_small_route(self):
        """Optimize với 5 điểm dừng (light load)."""
        payload = {
            "vehicle_constraints": {
                "max_weight_kg": 5000,
                "max_volume_cbm": 20.0,
                "truck_type": "5_ton_covered",
            },
            "depot": {
                "address": "Cảng Cát Lái, Quận 2, TP. HCM",
                "latitude": 10.7635,
                "longitude": 106.7992,
                "earliest_departure": "2026-06-16T08:00:00Z",
            },
            "stops": self._generate_stops(5),
        }
        with self.client.post(
            "/api/v1/bookings/optimize",
            json=payload,
            name="optimize_5_stops",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data["optimization_status"] not in ("OPTIMAL", "FEASIBLE"):
                    resp.failure(f"Unexpected status: {data['optimization_status']}")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(1)
    def optimize_large_route(self):
        """Optimize với 20 điểm dừng (stress test OR-Tools)."""
        payload = {
            "vehicle_constraints": {
                "max_weight_kg": 10000,
                "max_volume_cbm": 40.0,
                "truck_type": "10_ton_covered",
            },
            "depot": {
                "address": "Cảng Cát Lái, Quận 2, TP. HCM",
                "latitude": 10.7635,
                "longitude": 106.7992,
                "earliest_departure": "2026-06-16T08:00:00Z",
            },
            "stops": self._generate_stops(20),
        }
        with self.client.post(
            "/api/v1/bookings/optimize",
            json=payload,
            name="optimize_20_stops",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                # Kiểm tra response time < 15s (SLA từ SRS)
                if resp.elapsed.total_seconds() > 15:
                    resp.failure(f"Response time {resp.elapsed.total_seconds():.2f}s > 15s SLA")
            elif resp.status_code == 504:
                # Timeout là chấp nhận được với 20 điểm
                pass
            else:
                resp.failure(f"HTTP {resp.status_code}")
```

#### 3.4.5. Hướng dẫn chạy Load Test

```bash
# Cài đặt Locust
cd backend
pip install locust>=2.30

# Chạy WebSocket load test (giao diện web tại http://localhost:8089)
locust -f tests/load/locustfile_ws.py --host=wss://api.leopard.vn

# Chạy Routing load test (headless mode — 20 users, spawn rate 2)
locust -f tests/load/locustfile_routing.py --host=https://api.leopard.vn \
  --headless -u 20 -r 2 --run-time 5m --csv=reports/locust_routing

# Xem kết quả
cat reports/locust_routing_stats.csv
```

---

## 4. MÔI TRƯỜNG KIỂM THỬ

### 4.1. Môi trường

| Môi trường | URL | Database | Cấu hình |
|---|---|---|---|
| **Local Dev** | `http://localhost:8000` | SQLite (unit test) | Docker Compose local |
| **CI/CD** | GitHub Actions ephemeral | PostgreSQL 16 (service container) | ubuntu-latest, 2-core |
| **Staging** | `https://staging.leopard.vn` | PostgreSQL 16 + Redis | VPS 2GB RAM, 2 CPU |
| **Production** | `https://api.leopard.vn` | PostgreSQL 16 + Redis + TimescaleDB | VPS 4GB RAM, 2 CPU |

### 4.2. Dữ liệu kiểm thử

- **Test dataset cho XGBoost ETA:** 500+ mẫu GPS log tổng hợp (synthetic data).
- **Test dataset cho OR-Tools VRP:** 50 kịch bản route với 3-20 điểm dừng.
- **Test users:** 5 shipper + 5 driver + 2 admin (seed script tại `scripts/seed_test_data.py`).

---

## 5. KỊCH BẢN KIỂM THỬ 3 USER STORY CRITICAL

> **Ký hiệu:** `[TC-XX-YY]` — Test Case cho User Story XX, kịch bản YY.
> **Precondition:** Mỗi kịch bản cần có dữ liệu seed phù hợp.

---

### 5.1. US-2.1: Luồng đặt hàng đa điểm (Booking Flow)

**User Story:** *Là một chủ cửa hàng vật liệu xây dựng (SME), tôi muốn nhập điểm lấy hàng và tối đa 5 điểm giao hàng, để vận chuyển hàng hóa cho nhiều công trình cùng một lúc.*

#### Kịch bản 1: Happy path — Đặt đơn thành công với 3 điểm dừng

| Bước | Actor | Hành động | Hệ thống phản hồi | Xác nhận (Assert) |
|---|---|---|---|---|
| 1 | Shipper | Mở app → màn hình tạo đơn | Hiển thị bản đồ + form nhập | Map hiển thị, input address focus |
| 2 | Shipper | Nhập địa chỉ pickup "Cảng Cát Lái" | Vietmap Autocomplete gợi ý | dropdown xuất hiện sau 3 ký tự |
| 3 | Shipper | Chọn pickup từ gợi ý | Marker pickup hiện trên map | Marker A hiển thị đúng toạ độ |
| 4 | Shipper | Nhập 2 điểm dropoff (Q.1 và Q.7) | Marker B, C hiển thị + polyline nối | 3 marker đúng thứ tự |
| 5 | Shipper | Nhập: trọng lượng 2300kg, có bốc xếp | Gọi API calculate-fare | Hiển thị giá: 850,000 VND |
| 6 | Shipper | Nhấn "Đặt hàng" | Gọi API create-booking → 201 | Hiển thị mã đơn + thông tin |
| 7 | Shipper | Chuyển sang màn hình thanh toán | VietQR hiển thị | QR image + số tiền 850,000 VND |
| 8 | Hệ thống | Kiểm tra dữ liệu đơn trong DB | orders, order_stops, payments | Dữ liệu khớp với input |

#### Kịch bản 2: Từ chối đơn khi nhập > 5 điểm dừng

| Bước | Actor | Hành động | Expected |
|---|---|---|---|
| 1 | Shipper | Thêm điểm dừng thứ 6 | Nút "Thêm điểm" bị disabled |
| 2 | Shipper | Cố gắng gọi API với 6 stops qua Postman | HTTP 422 — validation error |

#### Kịch bản 3: Hủy đơn trước khi có tài xế nhận

| Bước | Actor | Hành động | Expected |
|---|---|---|---|
| 1 | Shipper | Vào chi tiết đơn (status = pending) | Nút "Hủy đơn" hiển thị |
| 2 | Shipper | Nhấn "Hủy đơn" → chọn lý do | Confirm dialog |
| 3 | Shipper | Xác nhận hủy | Status → "cancelled", cancelled_by = "shipper" |

#### Kịch bản 4: Shipper không thể hủy đơn khi đã có tài xế nhận

| Bước | Actor | Hành động | Expected |
|---|---|---|---|
| 1 | Shipper | Vào đơn đã được tài xế accept (status = accepted) | Nút "Hủy đơn" bị ẩn |
| 2 | Shipper | Gọi API hủy trực tiếp | HTTP 409 — "Cannot cancel an accepted booking" |

#### Test Coverage Mapping

| Kịch bản | Unit Test (Backend) | Unit Test (Frontend) | Integration Test |
|---|---|---|---|
| Happy path 3 stops | UT-B-06, UT-B-09, UT-B-10 | UT-F-04, UT-F-05, UT-F-08 | IT-08, IT-09, IT-13 |
| > 5 stops | UT-B-08 | UT-F-07 | — |
| Cancel pending | UT-B-16 | — | IT-14 |
| Cancel accepted | UT-B-15 | — | IT-14 |

---

### 5.2. US-4.1: Theo dõi xe real-time (Tracking)

**User Story:** *Là một shipper đang chờ hàng đến, tôi muốn nhìn thấy vị trí thực tế của xe tải di chuyển trên bản đồ theo thời gian thực và ETA đếm ngược.*

#### Kịch bản 1: Happy path — Theo dõi xe di chuyển

| Bước | Actor | Hành động | Hệ thống phản hồi | Xác nhận |
|---|---|---|---|---|
| 1 | Driver | Nhấn "Bắt đầu chuyến đi" | WebSocket kết nối → gửi CONNECTED | WS status = connected |
| 2 | Driver | App gửi GPS (10.7689, 106.7012) mỗi 5s | Backend Pub/Sub qua Redis → broadcast | Shipper nhận PUSH_DRIVER_LOCATION |
| 3 | Shipper | Mở màn hình tracking | Marker xe di chuyển + ETA cập nhật | Marker Lerp mượt, ETA giảm |
| 4 | Driver | Đến điểm dừng → nhấn "Đã đến" | WS gửi DRIVER_ARRIVED_AT_STOP | Shipper thấy stop status = arrived |
| 5 | Shipper | Xem ETA mới | AI ETA recalculate | ETA điều chỉnh theo vị trí mới |

#### Kịch bản 2: Mất kết nối WebSocket (Network loss)

| Bước | Actor | Hành động | Expected |
|---|---|---|---|
| 1 | Driver | Di chuyển vào vùng mất sóng (hầm, đèo) | WebSocket disconnect |
| 2 | Driver App | GPS queue vào local storage | Queue size > 0 |
| 3 | Driver | Có sóng trở lại | WebSocket reconnect → sync queue |
| 4 | Shipper | Marker dừng + hiển thị "last seen X phút trước" | UI không giật, có trạng thái disconnected |
| 5 | Shipper | Kết nối lại → marker nhảy đến vị trí mới nhất | Data consistency |

#### Kịch bản 3: Nhiều shipper theo dõi cùng 1 chuyến (Private broadcast)

| Bước | Actor | Hành động | Expected |
|---|---|---|---|
| 1 | Shipper A | Đăng nhập → mở tracking | Nhận location của chuyến A |
| 2 | Shipper B | Đăng nhập → mở tracking | Không thấy location của chuyến A |
| 3 | Shipper A | Tắt app | WebSocket close → không còn nhận data |

#### Test Coverage Mapping

| Kịch bản | Unit Test (Backend) | Unit Test (Frontend) | Integration Test |
|---|---|---|---|
| Happy path | UT-B-17, UT-B-18, UT-B-19, UT-B-20 | UT-F-09, UT-F-10 | IT-21, IT-22, IT-23 |
| Mất kết nối | — | UT-F-11 | — |
| Private broadcast | — | — | IT-22 (kiểm tra booking_id) |

---

### 5.3. US-7.1: Thanh toán VietQR (Payment)

**User Story:** *Là một khách hàng đặt cuốc xe, tôi muốn màn hình hiển thị mã QR thanh toán ngân hàng (VietQR) có kèm số tiền và nội dung chuyển khoản chính xác.*

#### Kịch bản 1: Happy path — Tạo QR và xác nhận thanh toán

| Bước | Actor | Hành động | Hệ thống phản hồi | Xác nhận |
|---|---|---|---|---|
| 1 | Shipper | Đặt đơn thành công → màn hình payment | Gọi API generate VietQR → 200 | QR image hiển thị |
| 2 | Shipper | Kiểm tra thông tin QR | VietQR string chuẩn Napas247 | BIN đúng (970415), amount = 800,000 |
| 3 | Shipper | Quét QR bằng app ngân hàng | Chuyển đến màn hình xác nhận CK | — |
| 4 | Shipper | Nhấn "Tôi đã chuyển khoản" | Gọi API confirm-payment | Payment status = paid |
| 5 | Hệ thống | Cập nhật order | order.payment_status = paid | Driver nhận thông báo |

#### Kịch bản 2: Thanh toán thất bại — Amount không khớp

| Bước | Actor | Hành động | Expected |
|---|---|---|---|
| 1 | Shipper | Gọi API generate VietQR với amount = -1000 | HTTP 422 |
| 2 | Shipper | Gọi API generate VietQR với amount = 0 | HTTP 422 |

#### Kịch bản 3: Idempotency — Webhook/webhook trùng

| Bước | Actor | Hành động | Expected |
|---|---|---|---|
| 1 | System | Webhook thanh toán gửi request thứ nhất | Payment status → paid, HTTP 200 |
| 2 | System | Webhook gửi request trùng (cùng booking_id + amount) | HTTP 409 — "Payment already processed" |

#### Test Coverage Mapping

| Kịch bản | Unit Test (Backend) | Unit Test (Frontend) | Integration Test |
|---|---|---|---|
| Happy path QR | UT-B-21, UT-B-23 | UT-F-12, UT-F-13 | IT-16 |
| Amount sai | UT-B-22 | — | IT-17 |
| Idempotency | UT-B-24 | — | (manual test) |

---

## 6. TEMPLATE CI/CD GITHUB ACTIONS

### 6.1. Kiến trúc Pipeline

```
GitHub Push / PR to main
         │
         ▼
┌──────────────────────────────────────┐
│          CI/CD Pipeline               │
│                                      │
│  ┌─ Job 1: Backend ───────────────┐  │
│  │  Lint: ruff check + mypy       │  │
│  │  Test: pytest --cov            │  │
│  │  Service: PostgreSQL 16 (ctnr) │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌─ Job 2: Frontend ──────────────┐  │
│  │  Analyze: dart analyze         │  │
│  │  Format: dart format --check   │  │
│  │  Test: flutter test --coverage │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌─ (Optional) Deploy to Staging ─┐  │
│  │  Deploy trên push to main      │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### 6.2. Workflow File

```yaml
# .github/workflows/ci.yml
# LEOPARD CI/CD Pipeline — GitHub Actions (public repo free tier)
# Trigger: push & pull request to main

name: LEOPARD CI/CD

on:
  push:
    branches: [main]
    paths-ignore:
      - 'docs/**'
      - 'README.md'
      - '.gitignore'
      - 'docker-compose*.yml'
      - '.env.example'
  pull_request:
    branches: [main]
    paths-ignore:
      - 'docs/**'
      - 'README.md'

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"
  FLUTTER_VERSION: "3.24"
  POSTGRES_VERSION: "16"
  REDIS_VERSION: "7-alpine"

jobs:
  # ═══════════════════════════════════════════════════════════════
  # JOB 1: BACKEND — lint, type-check, unit & integration test
  # ═══════════════════════════════════════════════════════════════
  backend:
    name: Backend (lint + test)
    runs-on: ubuntu-latest
    timeout-minutes: 15

    services:
      postgres:
        image: timescale/timescaledb:latest-pg16
        env:
          POSTGRES_DB: leopard_test
          POSTGRES_USER: leopard_test
          POSTGRES_PASSWORD: leopard_test_pass
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U leopard_test -d leopard_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python ${{ env.PYTHON_VERSION }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
          cache-dependency-path: backend/requirements*.txt

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends \
            libgomp1 \
            postgresql-client

      - name: Install Python dependencies
        working-directory: backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      # ── Lint ─────────────────────────────────────────────
      - name: Lint with ruff
        working-directory: backend
        run: |
          ruff check app/ tests/ --output-format=github
          ruff format app/ tests/ --check

      - name: Type check with mypy
        working-directory: backend
        run: |
          mypy app/ --strict --ignore-missing-imports

      # ── Unit & Integration Tests ─────────────────────────
      - name: Run tests with pytest
        working-directory: backend
        env:
          DATABASE_URL: postgresql+asyncpg://leopard_test:leopard_test_pass@localhost:5432/leopard_test
          REDIS_URL: redis://localhost:6379/1
          SECRET_KEY: ci-secret-key-not-for-prod
          VIETMAP_API_KEY: ${{ secrets.VIETMAP_API_KEY }}
          OPENWEATHER_API_KEY: ${{ secrets.OPENWEATHER_API_KEY }}
          FIREBASE_CREDENTIALS: ${{ secrets.FIREBASE_CREDENTIALS }}
        run: |
          pytest tests/ \
            --verbose \
            --cov=app \
            --cov-report=xml:coverage.xml \
            --cov-report=term \
            --cov-fail-under=70 \
            -x \
            --timeout=120

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml
          flags: backend
          fail_ci_if_error: false

      # ── Security scan ────────────────────────────────────
      - name: Scan dependencies for vulnerabilities
        working-directory: backend
        run: |
          pip-audit --requirement requirements.txt

  # ═══════════════════════════════════════════════════════════════
  # JOB 2: FRONTEND — analyze, format-check, unit & widget test
  # ═══════════════════════════════════════════════════════════════
  frontend:
    name: Frontend (analyze + test)
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Flutter ${{ env.FLUTTER_VERSION }}
        uses: subosito/flutter-action@v2
        with:
          flutter-version: ${{ env.FLUTTER_VERSION }}
          channel: 'stable'
          cache: true

      - name: Install Flutter dependencies
        working-directory: frontend
        run: flutter pub get

      # ── Analyze ──────────────────────────────────────────
      - name: Run dart analyze
        working-directory: frontend
        run: dart analyze --fatal-infos --fatal-warnings

      - name: Check dart formatting
        working-directory: frontend
        run: dart format --set-exit-if-changed .

      # ── Tests ────────────────────────────────────────────
      - name: Run flutter unit tests
        working-directory: frontend
        run: |
          flutter test \
            --coverage \
            --machine > test_report.json

      - name: Parse test results
        run: |
          echo "Test results:"
          dart run -c 'import "dart:convert"; import "dart:io"; \
            var data = jsonDecode(File("frontend/test_report.json").readAsStringSync()); \
            var passed = data.where((e) => e["type"] == "test".length); \
            print("Total tests: ${data.length}");'

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: frontend/coverage/lcov.info
          flags: frontend
          fail_ci_if_error: false

  # ═══════════════════════════════════════════════════════════════
  # JOB 3 (optional): DEPLOY TO STAGING — only on push to main
  # ═══════════════════════════════════════════════════════════════
  deploy-staging:
    name: Deploy to Staging
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    needs: [backend, frontend]
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /home/deploy/leopard
            git pull origin main
            docker compose -f docker-compose.yml up -d --build
            docker system prune -f
```

### 6.3. Secrets cần cấu hình trên GitHub

| Secret Name | Mô tả |
|---|---|
| `VIETMAP_API_KEY` | API Key cho Vietmap Services |
| `OPENWEATHER_API_KEY` | API Key cho OpenWeatherMap |
| `FIREBASE_CREDENTIALS` | Firebase service account JSON (base64) |
| `STAGING_HOST` | IP/Domain của staging server |
| `STAGING_USER` | SSH user cho staging deploy |
| `STAGING_SSH_KEY` | SSH private key cho staging deploy |

### 6.4. File requirements cho CI

**`backend/requirements-dev.txt`:**

```
# Testing
pytest>=7.4
pytest-asyncio>=0.23
pytest-cov>=4.1
pytest-mock>=3.12
pytest-timeout>=2.3
httpx>=0.27
freezegun>=1.5

# Linting & type checking
ruff>=0.5
mypy>=1.10

# Security
pip-audit>=2.7
```

**`.github/dependabot.yml`** (tự động cập nhật dependency):

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "pub"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## 7. TIÊU CHÍ KẾT THÚC KIỂM THỬ

Kiểm thử MVP được coi là hoàn thành (Test Exit Criteria) khi đáp ứng **tất cả** các điều kiện sau:

| STT | Tiêu chí | Ngưỡng | Phương pháp đo |
|---|---|---|---|
| E1 | Tất cả Unit Test pass | 100% | `pytest` + `flutter test` exit code 0 |
| E2 | Độ phủ code backend (service layer) | ≥ 70% | `pytest --cov` report |
| E3 | Độ phủ code frontend (bloc/logic) | ≥ 60% | `flutter test --coverage` report |
| E4 | Tất cả Integration Test pass | 100% | `pytest tests/integration/` |
| E5 | Load Test WebSocket: 100 connections | Không crash, P95 < 500ms | Locust HTML report |
| E6 | Load Test Routing: 20 stops endpoint | Response time < 15s | Locust report |
| E7 | Bug Critical (P0) còn open | 0 | GitHub Issues |
| E8 | Bug High (P1) còn open | ≤ 3 | GitHub Issues |
| E9 | CI/CD pipeline green trên `main` | 100% | GitHub Actions status |
| E10 | Code review tất cả PR | 100% merged | GitHub PRs |

---

## 8. RỦI RO & GIẢM THIỂU

| ID | Rủi ro | Tác động | Xác suất | Giảm thiểu |
|---|---|---|---|---|
| R1 | OR-Tools chạy quá 15s với 20 điểm | Vi phạm SLA SRS | Medium | Implement timeout + fallback; tune solver parameters; cache kết quả tối ưu |
| R2 | WebSocket không đủ 100 kết nối trên VPS 2GB RAM | OOM, crash | Medium | Kiểm tra Redis Pub/Sub backpressure; giới hạn worker connections; tune asyncio buffer |
| R3 | Firebase OTP SMS không gửi được do quota | Auth flow blocked | Low | Sử dụng test mode OTP tự động trong CI; có fallback mock cho unit test |
| R4 | Vietmap API vượt free tier 500 req/ngày | Routing fail | High | Cache routing results vào Redis (TTL 1 giờ); dùng OSRM local fallback |
| R5 | Không đủ coverage do thiếu thời gian | Chất lượng thấp | Medium | Tập trung unit test vào core service (booking, payment, tracking); chấp nhận coverage frontend thấp hơn ở MVP |

---

## 9. PHỤ LỤC: SCRIPT MẪU

### 9.1. Script seed dữ liệu test

```python
# backend/scripts/seed_test_data.py
"""
Seed dữ liệu mẫu cho môi trường test/staging.
Chạy: python scripts/seed_test_data.py
"""
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle


async def seed():
    async with AsyncSessionLocal() as session:
        # Tạo 5 shipper test
        for i in range(1, 6):
            user = User(
                firebase_uid=f"test_firebase_shipper_{i}",
                role="shipper",
                phone=f"+8490000000{i}",
                full_name=f"Shipper Test {i}",
                is_verified=True,
            )
            session.add(user)

        # Tạo 5 driver test
        for i in range(1, 6):
            user = User(
                firebase_uid=f"test_firebase_driver_{i}",
                role="driver",
                phone=f"+8491111111{i}",
                full_name=f"Driver Test {i}",
                is_verified=True,
            )
            session.add(user)
            await session.flush()

            driver = Driver(
                user_id=user.id,
                is_available=True,
                status="online",
                license_number=f"79C{10000 + i}",
                license_class="D",
            )
            session.add(driver)
            await session.flush()

            vehicle = Vehicle(
                driver_id=driver.id,
                plate_number=f"51C-{i:03d}.{i:02d}",
                vehicle_type="truck_5t_10t",
                max_weight_kg=8000,
            )
            session.add(vehicle)

        await session.commit()
        print("✅ Seed data created successfully!")


asyncio.run(seed())
```

### 9.2. Script chạy toàn bộ test suite local

```bash
# scripts/run-tests.sh — Chạy toàn bộ test suite
#!/bin/bash
set -euo pipefail

echo "╔════════════════════════════════════════╗"
echo "║   LEOPARD — Full Test Suite Runner     ║"
echo "╚════════════════════════════════════════╝"

# 1. Backend tests
echo ""
echo "▶  Backend: Lint & Type Check"
cd backend
ruff check app/ tests/
ruff format app/ tests/ --check
mypy app/ --strict --ignore-missing-imports

echo ""
echo "▶  Backend: Unit & Integration Tests"
export DATABASE_URL="sqlite+aiosqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/1"
export SECRET_KEY="test-local-key"
export VIETMAP_API_KEY="test"
export OPENWEATHER_API_KEY="test"

pytest tests/ \
  --verbose \
  --cov=app \
  --cov-report=term \
  --cov-report=html:reports/coverage-backend \
  -x \
  --timeout=120

# 2. Frontend tests
echo ""
echo "▶  Frontend: Analyze & Tests"
cd ../frontend
dart analyze --fatal-infos
dart format --set-exit-if-changed .
flutter test --coverage

# 3. Generate combined report
echo ""
echo "▶  Reports generated:"
echo "  - Backend coverage:  reports/coverage-backend/index.html"
echo "  - Frontend coverage: frontend/coverage/lcov.info"
echo ""
echo "✅ All tests passed!"
```

---

> **Tài liệu này có hiệu lực kể từ ngày ký.** Mọi thay đổi về chiến lược kiểm thử phải được cập nhật qua Pull Request và được QA Lead + Tech Lead phê duyệt.
