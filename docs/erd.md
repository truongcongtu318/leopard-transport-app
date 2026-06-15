# ERD — ENTITY RELATIONSHIP DIAGRAM & DATABASE DESIGN
## DỰ ÁN: LEOPARD - HỆ THỐNG KẾT NỐI VẬN TẢI HÀNG HÓA TRỌNG TẢI LỚN

| Field | Value |
|---|---|
| **Tên tài liệu** | Entity Relationship Diagram & Database Schema Design |
| **Dự án** | LEOPARD APP |
| **Phiên bản** | 1.0 |
| **Ngày tạo** | 2026-06-15 |
| **Cơ sở dữ liệu** | PostgreSQL 16 + PostGIS + TimescaleDB + Redis |
| **Tác giả** | Tech Lead Team LEOPARD |
| **Trạng thái** | Draft / Ready for Review |

---

## 1. TỔNG QUAN KIẾN TRÚC DỮ LIỆU (DATA ARCHITECTURE OVERVIEW)

### 1.1. Chiến lược phân tầng

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LEOPARD DATA ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📦 PostgreSQL 16  (Single source of truth)                        │
│  ├── OLTP Schema:  `public`   (users, orders, payments)            │
│  ├── GIS Schema:   (PostGIS)  (locations, routes, geofences)       │
│  └── Time-Series:  (TimescaleDB)  (gps_tracking hypertable)        │
│                                                                     │
│  ⚡ Redis 7  (Cache & Real-time layer)                              │
│  ├── Cache:     driver:location:{id} → GeoJSON                      │
│  ├── Pub/Sub:   tracking:{order_id} → location_broadcast            │
│  └── Rate Limit: tokens bucket                                     │
│                                                                     │
│  🗄️ Object Storage (Local filesystem / S3 sau này)                  │
│  └── driver_documents, order_images, avatar                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2. Quy tắc đặt tên (Naming Conventions)

| Quy tắc | Áp dụng cho | Ví dụ |
|---|---|---|
| **snake_case** | Tên bảng, cột, index, constraint | `order_stops`, `driver_id` |
| **số nhiều** | Tên bảng (table name) | `users`, `orders`, `payments` |
| **số ít** | Tên cột (column name) | `user_id`, `vehicle_type` |
| **IX_** prefix | Index name | `IX_orders_shipper_id_status` |
| **FK_** prefix | Foreign key name | `FK_orders_shipper_id` |
| **UQ_** prefix | Unique constraint | `UQ_users_firebase_uid` |
| **CHK_** prefix | Check constraint | `CHK_payments_amount_positive` |
| **created_at** | Timestamp tạo record | `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` |
| **updated_at** | Timestamp cập nhật gần nhất | `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` |

### 1.3. Chuẩn hoá dữ liệu (Normalization Level)

- Thiết kế đạt **3NF (Third Normal Form)** cho Core Business Entities (`orders`, `payments`, `users`).
- Cho phép **JSONB** Denormalization ở những bảng cần tốc độ query nhanh mà không muốn JOIN quá nhiều bảng, ví dụ:
  - `order_stops.address` (JSONB) — lưu địa chỉ full text + toạ độ thay vì JOIN vào bảng addresses riêng (vì mỗi địa chỉ chỉ dùng 1 lần cho 1 đơn hàng, không có tái sử dụng).
- **EVENTUAL CONSISTENCY** chấp nhận cho real-time tracking data (có thể mất 1-2 tick GPS).

---

## 2. DANH SÁCH CÁC ENTITY (ENTITY LIST)

| STT | Entity (Bảng) | Loại | Mô tả |
|---|---|---|---|
| 1 | `users` | Core | Tất cả người dùng hệ thống (Shipper, Driver, Admin, FleetOwner) |
| 2 | `drivers` | Core | Hồ sơ mở rộng cho tài xế (1-1 với users) |
| 3 | `driver_documents` | Core | Hồ sơ giấy tờ định kỳ của tài xế (GPLX, Đăng kiểm, Bảo hiểm) |
| 4 | `vehicles` | Core | Thông tin xe của tài xế |
| 5 | `businesses` | Core | Thông tin doanh nghiệp SME (Fleet Owner) |
| 6 | `business_contracts` | Transaction | Hợp đồng định kỳ giữa doanh nghiệp và LEOPARD |
| 7 | `business_drivers` | Junction | Liên kết tài xế thuộc đội xe của doanh nghiệp nào |
| 8 | `orders` | Transaction | Đơn hàng vận chuyển |
| 9 | `order_stops` | Transaction | Các điểm dừng trong đơn hàng (Pickup, Dropoff, Midpoint) |
| 10 | `order_items` | Transaction | Danh sách hàng hoá trong đơn |
| 11 | `order_bids` | Transaction | Giá chào của tài xế cho đơn hàng (nếu là cơ chế đấu giá) |
| 12 | `payments` | Transaction | Giao dịch thanh toán cho đơn hàng |
| 13 | `active_trips` | Stateful | Trạng thái đang chạy của chuyến đi (cập nhật realtime) |
| 14 | `gps_tracking` | Time-Series | Lịch sử toạ độ GPS của tài xế (TimescaleDB Hypertable) |
| 15 | `eta_predictions` | Transaction | Kết quả dự báo ETA của model AI |
| 16 | `route_optimizations` | Transaction | Kết quả tối ưu VRP của OR-Tools |
| 17 | `notifications` | Transaction | Lịch sử thông báo push cho người dùng |

---

## 3. CHI TIẾT TỪNG ENTITY (ENTITY DETAIL DESIGN)

### 3.1. `users` — Bảng người dùng trung tâm

```sql
CREATE TABLE users (
    id                BIGSERIAL       PRIMARY KEY,
    firebase_uid      VARCHAR(128)    NOT NULL,
    role              VARCHAR(20)     NOT NULL DEFAULT 'shipper'
                                      CHECK (role IN ('shipper','driver','fleet_owner','admin')),
    phone             VARCHAR(15)     NOT NULL,
    email             VARCHAR(255),
    full_name         VARCHAR(120)    NOT NULL,
    avatar_url        VARCHAR(512),
    is_verified       BOOLEAN         NOT NULL DEFAULT FALSE,
    is_active         BOOLEAN         NOT NULL DEFAULT TRUE,
    last_login_at     TIMESTAMPTZ,
    metadata          JSONB           DEFAULT '{}',
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT UQ_users_firebase_uid UNIQUE (firebase_uid),
    CONSTRAINT UQ_users_phone        UNIQUE (phone)
);

-- Indexes
CREATE INDEX IX_users_role           ON users (role) WHERE is_active = TRUE;
CREATE INDEX IX_users_created_at     ON users (created_at DESC);
CREATE INDEX IX_users_phone_lookup   ON users (phone) INCLUDE (id, full_name, role);
```

**Giải thích thiết kế:**
- `firebase_uid`: Khóa ngoại tham chiếu đến Firebase Auth. Firebase cung cấp xác thực, JWT và session management, nhưng dữ liệu profile chi tiết lưu ở PostgreSQL.
- `role`: Enum stored dạng string (không dùng enum type của PG vì dễ migrate về sau).
- `metadata`: JSONB linh hoạt để lưu các preference: `{"lang":"vi","notif_enabled":true,"fleet_id":null}`.
- **Phân biệt Shipper vs Driver:** Cả 2 là 1 user có role khác nhau. Tuy nhiên 1 user có thể vừa là shipper vừa là tài xế? Không hỗ trợ trong phase 1. Mỗi tài khoản chỉ có 1 role.

---

### 3.2. `drivers` — Hồ sơ mở rộng tài xế

```sql
CREATE TABLE drivers (
    id                  BIGSERIAL       PRIMARY KEY,
    user_id             BIGINT          NOT NULL,
    vehicle_id          BIGINT,                         -- FK đến vehicles (nullable: chưa có xe)
    license_number      VARCHAR(30),                    -- Số GPLX
    license_class       VARCHAR(5),                     -- Hạng B2, C, D, E, F
    license_expiry      DATE,
    id_card_number      VARCHAR(20),                    -- CCCD / CMND
    id_card_issue_date  DATE,
    id_card_issue_place VARCHAR(120),
    current_location    GEOGRAPHY(POINT, 4326),         -- PostGIS: Vị trí hiện tại
    is_available        BOOLEAN         NOT NULL DEFAULT TRUE,
    rating_sum          INTEGER         NOT NULL DEFAULT 0,
    rating_count        INTEGER         NOT NULL DEFAULT 0,
    total_trips         INTEGER         NOT NULL DEFAULT 0,
    total_distance_km   NUMERIC(10,2)   NOT NULL DEFAULT 0,
    total_earnings      NUMERIC(12,0)   NOT NULL DEFAULT 0,
    status              VARCHAR(20)     NOT NULL DEFAULT 'offline'
                        CHECK (status IN ('offline','online','on_trip','suspended')),
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_drivers_user_id      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT UQ_drivers_user_id      UNIQUE (user_id),
    CONSTRAINT CHK_drivers_rating      CHECK (rating_sum >= 0 AND rating_count >= 0),
    CONSTRAINT CHK_drivers_earnings    CHECK (total_earnings >= 0)
);

-- Indexes
CREATE INDEX IX_drivers_location       ON drivers USING GIST (current_location);
CREATE INDEX IX_drivers_available       ON drivers (is_available, status)
                                         WHERE is_available = TRUE AND status = 'online';
CREATE INDEX IX_drivers_vehicle_type    ON drivers (vehicle_id) INCLUDE (is_available);
CREATE INDEX IX_drivers_rating          ON drivers ((CASE WHEN rating_count > 0
                                            THEN rating_sum::FLOAT / rating_count
                                            ELSE 0 END) DESC);
```

**Giải thích thiết kế:**
- `current_location` dùng kiểu **GEOGRAPHY(POINT, 4326)** của PostGIS để hỗ trợ truy vấn tìm tài xế gần nhất (KNN search) bằng `ST_DWithin` và `ST_DistanceSphere`.
- `rating_sum / rating_count`: Lưu tổng điểm và số lượt đánh giá thay vì lưu rating trung bình float dễ sai số làm tròn khi tính toán đồng thời (concurrent update).
- `total_earnings` là **denormalized** (có thể tính từ bảng payments), được cache lại để tăng tốc hiển thị dashboard tài xế.
- `is_available` và `status` có partial index để tối ưu query: "Tìm tất cả tài xế online và sẵn sàng nhận đơn".

---

### 3.3. `driver_documents` — Hồ sơ giấy tờ tài xế

```sql
CREATE TABLE driver_documents (
    id              BIGSERIAL       PRIMARY KEY,
    driver_id       BIGINT          NOT NULL,
    doc_type        VARCHAR(20)     NOT NULL
                    CHECK (doc_type IN (
                        'driver_license_front', 'driver_license_back',
                        'id_card_front', 'id_card_back',
                        'vehicle_registration', 'vehicle_inspection',
                        'insurance_civil', 'insurance_cargo'
                    )),
    doc_url         VARCHAR(512)    NOT NULL,
    doc_metadata    JSONB           DEFAULT '{}',
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    rejected_reason TEXT,
    reviewed_by     BIGINT,                         -- admin user_id
    reviewed_at     TIMESTAMPTZ,
    expires_at      DATE,                           -- ngày hết hạn (vd: đăng kiểm 6 tháng)
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_driver_docs_driver     FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    CONSTRAINT FK_driver_docs_reviewer   FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IX_driver_docs_driver_status ON driver_documents (driver_id, status);
-- Index cho auto-expire: tìm giấy tờ sắp hết hạn để gửi thông báo
CREATE INDEX IX_driver_docs_expiring      ON driver_documents (expires_at)
                                            WHERE status = 'approved' AND expires_at IS NOT NULL;
```

**Giải thích thiết kế:**
- `doc_type` là enum giới hạn. Mỗi loại giấy tờ có thể upload mặt trước/sau riêng.
- `status` quản lý vòng đời: `pending → approved/rejected → expired`.
- `expires_at` cho phép hệ thống tự động gửi push notification nhắc tài xế gia hạn giấy tờ sắp hết hạn.
- Ảnh giấy tờ lưu trên filesystem/local storage (object storage sau này), `doc_url` là đường dẫn file.

---

### 3.4. `vehicles` — Thông tin phương tiện

```sql
CREATE TABLE vehicles (
    id                  BIGSERIAL       PRIMARY KEY,
    driver_id           BIGINT          NOT NULL,
    plate_number        VARCHAR(15)     NOT NULL,
    brand               VARCHAR(50),
    model               VARCHAR(50),
    year                SMALLINT,
    color               VARCHAR(30),
    vehicle_type        VARCHAR(20)     NOT NULL
                        CHECK (vehicle_type IN (
                            'three_wheeler',     -- xe ba gác
                            'truck_under_2t',    -- xe tải < 2 tấn
                            'truck_2t_5t',       -- 2-5 tấn
                            'truck_5t_10t',      -- 5-10 tấn
                            'truck_over_10t',    -- > 10 tấn
                            'container'          -- container
                        )),
    max_weight_kg       NUMERIC(7,2)    NOT NULL,
    max_volume_m3       NUMERIC(6,2),
    max_height_m        NUMERIC(4,2),               -- Chiều cao tối đa (m)
    max_width_m         NUMERIC(4,2),
    max_length_m        NUMERIC(4,2),
    has_lift_gate       BOOLEAN         NOT NULL DEFAULT FALSE,
    has_loading_ramp    BOOLEAN         NOT NULL DEFAULT FALSE,
    insurance_number    VARCHAR(50),
    insurance_expiry    DATE,
    inspection_expiry   DATE,
    vehicle_front_img   VARCHAR(512),
    vehicle_side_img    VARCHAR(512),
    status              VARCHAR(20)     NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'maintenance', 'retired', 'pending_approval')),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_vehicles_driver     FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    CONSTRAINT UQ_vehicles_plate      UNIQUE (plate_number),
    CONSTRAINT CHK_vehicles_weight    CHECK (max_weight_kg > 0),
    CONSTRAINT CHK_vehicles_height    CHECK (max_height_m IS NULL OR max_height_m > 0)
);

CREATE INDEX IX_vehicles_driver        ON vehicles (driver_id);
CREATE INDEX IX_vehicles_type_status   ON vehicles (vehicle_type, status);
CREATE INDEX IX_vehicles_inspection    ON vehicles (inspection_expiry)
                                        WHERE inspection_expiry IS NOT NULL;
```

**Giải thích thiết kế:**
- `vehicle_type` phân loại chi tiết để backend có thể match đơn hàng phù hợp với loại xe.
- Các trường `max_height_m`, `max_width_m`, `max_length_m` rất quan trọng để kiểm tra ràng buộc khi tài xế chạy qua cầu thấp/đường hẹp.
- `has_lift_gate / has_loading_ramp`: Hỗ trợ bốc xếp — là tiêu chí filter khi shipper có yêu cầu bốc xếp hàng.

---

### 3.5. `businesses` — Thông tin doanh nghiệp (Fleet Owner)

```sql
CREATE TABLE businesses (
    id                  BIGSERIAL       PRIMARY KEY,
    owner_id            BIGINT          NOT NULL,
    company_name        VARCHAR(200)    NOT NULL,
    tax_code            VARCHAR(20)     NOT NULL,
    business_address    JSONB           NOT NULL DEFAULT '{}',
    business_phone      VARCHAR(15),
    business_email      VARCHAR(255),
    logo_url            VARCHAR(512),
    contract_tier       VARCHAR(20)     NOT NULL DEFAULT 'basic'
                        CHECK (contract_tier IN ('basic', 'premium', 'enterprise')),
    is_verified         BOOLEAN         NOT NULL DEFAULT FALSE,
    max_drivers         INTEGER         NOT NULL DEFAULT 5,
    max_vehicles        INTEGER         NOT NULL DEFAULT 5,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_businesses_owner     FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT UQ_businesses_tax_code  UNIQUE (tax_code)
);

CREATE INDEX IX_businesses_owner       ON businesses (owner_id);
```

---

### 3.6. `business_contracts` — Hợp đồng doanh nghiệp

```sql
CREATE TABLE business_contracts (
    id                  BIGSERIAL       PRIMARY KEY,
    business_id         BIGINT          NOT NULL,
    contract_type       VARCHAR(30)     NOT NULL
                        CHECK (contract_type IN ('monthly_fixed', 'per_order', 'hybrid')),
    start_date          DATE            NOT NULL,
    end_date            DATE,
    monthly_fee         NUMERIC(12,0),
    per_order_fee       NUMERIC(12,0),
    discount_rate       NUMERIC(3,2)    DEFAULT 0,
    status              VARCHAR(20)     NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'expired', 'cancelled', 'renewed')),
    signed_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_contracts_business   FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE
);

CREATE INDEX IX_contracts_business_active ON business_contracts (business_id)
                                            WHERE status = 'active';
```

---

### 3.7. `business_drivers` — Liên kết tài xế thuộc doanh nghiệp

```sql
CREATE TABLE business_drivers (
    id                  BIGSERIAL       PRIMARY KEY,
    business_id         BIGINT          NOT NULL,
    driver_id           BIGINT          NOT NULL,
    role                VARCHAR(20)     NOT NULL DEFAULT 'driver'
                        CHECK (role IN ('driver', 'manager', 'owner')),
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    joined_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    left_at             TIMESTAMPTZ,

    CONSTRAINT FK_bizdrivers_business   FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    CONSTRAINT FK_bizdrivers_driver     FOREIGN KEY (driver_id)   REFERENCES drivers(id) ON DELETE CASCADE,
    CONSTRAINT UQ_bizdrivers_pair       UNIQUE (business_id, driver_id)
);

CREATE INDEX IX_bizdrivers_business      ON business_drivers (business_id, is_active);
```

---

### 3.8. `orders` — Bảng đơn hàng trung tâm (bảng quan trọng nhất)

```sql
CREATE TABLE orders (
    id                  BIGSERIAL       PRIMARY KEY,
    order_code          VARCHAR(20)     NOT NULL,       -- Mã đơn hàng hiển thị: LEOPARD-XXXXX
    shipper_id          BIGINT          NOT NULL,
    driver_id           BIGINT,                         -- Được gán sau khi có tài xế nhận đơn
    business_id         BIGINT,                         -- Nếu đơn thuộc doanh nghiệp
    vehicle_type_req    VARCHAR(20),                    -- Loại xe yêu cầu (nullable: auto match)
    status              VARCHAR(30)     NOT NULL DEFAULT 'pending'
                        CHECK (status IN (
                            'draft',              -- Đang soạn, chưa gửi
                            'pending',            -- Chờ tài xế nhận
                            'bidding',            -- Đang đấu giá
                            'accepted',           -- Tài xế đã nhận
                            'pickup_in_progress', -- Đang đến điểm lấy hàng
                            'in_transit',         -- Đang vận chuyển
                            'delivered',          -- Đã giao xong
                            'completed',          -- Hoàn tất + thanh toán
                            'cancelled',          -- Đã hủy
                            'disputed'            -- Có tranh chấp
                        )),
    total_price         NUMERIC(12,0)   NOT NULL DEFAULT 0,
    final_price         NUMERIC(12,0),                 -- Giá sau khi có điều chỉnh (nếu có)
    distance_km         NUMERIC(8,2),                  -- Tổng quãng đường
    estimated_duration_min INTEGER,                    -- ETA dự kiến (phút)
    actual_duration_min   INTEGER,                    -- Thời gian thực tế
    payment_method      VARCHAR(20)     NOT NULL DEFAULT 'bank_transfer'
                        CHECK (payment_method IN ('bank_transfer', 'cod', 'business_credit')),
    payment_status      VARCHAR(20)     NOT NULL DEFAULT 'unpaid'
                        CHECK (payment_status IN ('unpaid', 'paid', 'partial', 'refunded', 'cancelled')),
    pickup_notes        TEXT,
    requires_loading    BOOLEAN         NOT NULL DEFAULT FALSE,
    requires_unloading  BOOLEAN         NOT NULL DEFAULT FALSE,
    shipper_rating      SMALLINT        CHECK (shipper_rating BETWEEN 1 AND 5),
    driver_rating       SMALLINT        CHECK (driver_rating BETWEEN 1 AND 5),
    shipper_comment     TEXT,
    driver_comment      TEXT,
    cancelled_by        VARCHAR(20)     CHECK (cancelled_by IN ('shipper', 'driver', 'system', 'admin')),
    cancel_reason       TEXT,
    polylines           JSONB,                          -- Cache kết quả route polyline (để vẽ map)
    metadata            JSONB           DEFAULT '{}',
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_orders_shipper         FOREIGN KEY (shipper_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT FK_orders_driver          FOREIGN KEY (driver_id)  REFERENCES drivers(id) ON DELETE SET NULL,
    CONSTRAINT FK_orders_business        FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE SET NULL,
    CONSTRAINT UQ_orders_code            UNIQUE (order_code),
    CONSTRAINT CHK_orders_price          CHECK (total_price >= 0),
    CONSTRAINT CHK_orders_dates          CHECK (created_at <= updated_at)
);

-- Critical Indexes
CREATE INDEX IX_orders_shipper_status    ON orders (shipper_id, status);
CREATE INDEX IX_orders_driver_status     ON orders (driver_id, status) WHERE driver_id IS NOT NULL;
CREATE INDEX IX_orders_status_created    ON orders (status, created_at DESC);
CREATE INDEX IX_orders_business          ON orders (business_id, created_at DESC) WHERE business_id IS NOT NULL;
CREATE INDEX IX_orders_payment_status    ON orders (payment_method, payment_status)
                                          WHERE payment_status IN ('unpaid', 'partial');
-- Index cho dashboard: tìm đơn đang active
CREATE INDEX IX_orders_active            ON orders (driver_id, status)
                                          WHERE status IN ('pickup_in_progress', 'in_transit');
```

**Giải thích thiết kế bảng `orders` (bảng quan trọng nhất hệ thống):**

1. **State Machine (status):** 11 trạng thái với flow rõ ràng:
   ```
   draft → pending → bidding → accepted → pickup_in_progress → in_transit → delivered → completed
                                                                                    ↕
                                                                              disputed
   ```
   Mỗi lần chuyển trạng thái đều phải ghi vào bảng `order_status_logs` (xem mục 5. Audit Log).

2. **shipper_id và driver_id:** Có FK đến users (cho shipper) và drivers (cho tài xế). Đây là 2 entity khác nhau dù cùng extends từ users. Quyết định này tránh nhầm lẫn khi JOIN.

3. **polylines (JSONB):** Cache kết quả route từ Vietmap/OSRM. Lưu thẳng vào order để khi cần vẽ lại map tracking, không cần gọi lại API routing.

4. **Index strategy:**
   - `IX_orders_shipper_status`: Query nhanh "đơn của tôi" cho shipper.
   - `IX_orders_driver_status`: Query nhanh "đơn của tôi" cho tài xế.
   - `IX_orders_active`: Partial index chỉ lưu đơn đang chạy — lightweight.
   - `IX_orders_payment_status`: Tìm đơn chưa thanh toán để gửi reminder.

---

### 3.9. `order_stops` — Các điểm dừng trong đơn hàng

```sql
CREATE TABLE order_stops (
    id                  BIGSERIAL       PRIMARY KEY,
    order_id            BIGINT          NOT NULL,
    stop_type           VARCHAR(15)     NOT NULL
                        CHECK (stop_type IN ('pickup', 'dropoff', 'midpoint')),
    sequence_order      SMALLINT        NOT NULL,      -- 1, 2, 3...
    address_text        TEXT            NOT NULL,       -- Địa chỉ dạng text
    address_components  JSONB           DEFAULT '{}',   -- { "province": "HCM", "district": "Q7", "ward": "..." }
    latitude            NUMERIC(10,7)   NOT NULL,
    longitude           NUMERIC(10,7)   NOT NULL,
    contact_name        VARCHAR(120),
    contact_phone       VARCHAR(15),
    contact_notes       TEXT,
    arrived_at          TIMESTAMPTZ,                    -- Thời gian đến điểm này thực tế
    departed_at         TIMESTAMPTZ,                   -- Thời gian rời khỏi
    proof_image_url     VARCHAR(512),                   -- Ảnh chụp chứng minh đã giao
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_orderstops_order      FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT CHK_orderstops_seq       CHECK (sequence_order >= 1),
    CONSTRAINT UQ_orderstops_order_seq  UNIQUE (order_id, sequence_order)
);

CREATE INDEX IX_orderstops_order         ON order_stops (order_id, sequence_order);
CREATE INDEX IX_orderstops_location      ON order_stops USING GIST (
                                            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326));
```

**Giải thích thiết kế:**
- `stop_type` + `sequence_order`: Xác định thứ tự các điểm. Ví dụ: `pickup(1)` → `dropoff(2)` hoặc `pickup(1)` → `midpoint(2)` → `dropoff(3)`.
- `arrived_at` / `departed_at`: Ghi lại timeline của chuyến đi để tính toán actual duration.
- `proof_image_url`: Tài xế chụp ảnh hàng hóa tại điểm giao để làm bằng chứng giao hàng thành công.
- `address_components` (JSONB): Lưu thông tin địa lý phân cấp để sau này thống kê theo khu vực (vd: "tổng số đơn giao tại Q.7 trong tháng 9").

---

### 3.10. `order_items` — Hàng hoá trong đơn

```sql
CREATE TABLE order_items (
    id                  BIGSERIAL       PRIMARY KEY,
    order_stop_id       BIGINT,                         -- nullable: hàng giao ở điểm nào
    order_id            BIGINT          NOT NULL,
    description         VARCHAR(500)    NOT NULL,
    category            VARCHAR(50),                    -- "vlxd", "nong_san", "thuc_pham", "noi_that", ...
    weight_kg           NUMERIC(8,2),
    quantity            INTEGER         NOT NULL DEFAULT 1,
    unit_type           VARCHAR(30)     DEFAULT 'piece',-- "kg", "m3", "pallet", "piece"
    length_cm           NUMERIC(6,2),
    width_cm            NUMERIC(6,2),
    height_cm           NUMERIC(6,2),
    is_fragile          BOOLEAN         NOT NULL DEFAULT FALSE,
    is_stackable        BOOLEAN         NOT NULL DEFAULT TRUE,
    requires_cooling    BOOLEAN         NOT NULL DEFAULT FALSE,
    image_urls          JSONB           DEFAULT '[]',   -- ["url1","url2",...]
    special_instructions TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_orderitems_order       FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT FK_orderitems_stop        FOREIGN KEY (order_stop_id) REFERENCES order_stops(id) ON DELETE SET NULL,
    CONSTRAINT CHK_orderitems_weight     CHECK (weight_kg IS NULL OR weight_kg > 0)
);

CREATE INDEX IX_orderitems_order         ON order_items (order_id);
```

**Giải thích thiết kế:**
- `category` cho phép phân loại hàng hoá để thống kê: "Loại hàng nào được vận chuyển nhiều nhất?"
- Các trường `length_cm`, `width_cm`, `height_cm`: Check ràng buộc thể tích với thùng xe.
- `is_fragile`, `is_stackable`, `requires_cooling`: Các flag này giúp backend kiểm tra tài xế có đủ điều kiện chuyên chở hay không.

---

### 3.11. `order_bids` — Giá chào của tài xế (tính năng đấu giá)

```sql
CREATE TABLE order_bids (
    id                  BIGSERIAL       PRIMARY KEY,
    order_id            BIGINT          NOT NULL,
    driver_id           BIGINT          NOT NULL,
    bid_price           NUMERIC(12,0)   NOT NULL,
    bid_notes           TEXT,
    status              VARCHAR(20)     NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'accepted', 'rejected', 'withdrawn')),
    responded_at        TIMESTAMPTZ,                    -- Shipper accept/reject time
    expires_at          TIMESTAMPTZ     NOT NULL,        -- Hết hạn chào giá
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_orderbids_order           FOREIGN KEY (order_id)   REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT FK_orderbids_driver          FOREIGN KEY (driver_id)  REFERENCES drivers(id) ON DELETE CASCADE,
    CONSTRAINT UQ_orderbids_order_driver    UNIQUE (order_id, driver_id)
);

CREATE INDEX IX_orderbids_order_price  ON order_bids (order_id, bid_price);
```

---

### 3.12. `payments` — Giao dịch thanh toán

```sql
CREATE TABLE payments (
    id                  BIGSERIAL       PRIMARY KEY,
    order_id            BIGINT          NOT NULL,
    payer_id            BIGINT          NOT NULL,        -- user_id của người trả tiền
    receiver_id         BIGINT          NOT NULL,        -- user_id của người nhận tiền (tài xế / doanh nghiệp)
    amount              NUMERIC(12,0)   NOT NULL,
    platform_fee        NUMERIC(12,0)   NOT NULL DEFAULT 0,  -- Phí sàn LEOPARD
    driver_earnings     NUMERIC(12,0)   NOT NULL DEFAULT 0,  -- Số tiền tài xế thực nhận
    method              VARCHAR(20)     NOT NULL
                        CHECK (method IN ('bank_transfer', 'cod', 'business_credit', 'wallet')),
    status              VARCHAR(20)     NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'completed', 'failed', 'refunded', 'cancelled')),
    bank_code           VARCHAR(10),                    -- Mã ngân hàng (VietQR)
    bank_account_no     VARCHAR(30),                    -- Số tài khoản nhận
    qr_code_url         VARCHAR(512),                   -- URL mã VietQR đã sinh
    transaction_id      VARCHAR(100),                    -- Mã giao dịch từ ngân hàng (nếu có webhook)
    cod_collected       BOOLEAN         NOT NULL DEFAULT FALSE,  -- Đã thu COD chưa?
    notes               TEXT,
    paid_at             TIMESTAMPTZ,                    -- Thời điểm thanh toán thành công
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_payments_order         FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE RESTRICT,
    CONSTRAINT FK_payments_payer         FOREIGN KEY (payer_id)   REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT FK_payments_receiver      FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT CHK_payments_amount       CHECK (amount > 0),
    CONSTRAINT CHK_payments_fee          CHECK (platform_fee >= 0),
    CONSTRAINT CHK_payments_earnings     CHECK (driver_earnings >= 0)
);

CREATE INDEX IX_payments_order           ON payments (order_id);
CREATE INDEX IX_payments_payer           ON payments (payer_id, created_at DESC);
CREATE INDEX IX_payments_receiver        ON payments (receiver_id, status, created_at DESC);
CREATE INDEX IX_payments_status          ON payments (status) WHERE status = 'pending';
```

**Giải thích thiết kế:**
- `platform_fee` và `driver_earnings`: Tách biệt số tiền shipper trả, phí sàn và tiền tài xế nhận. Điều này quan trọng cho đối soát và báo cáo tài chính.
- `transaction_id`: Reserved cho tương lai khi tích hợp webhook ngân hàng (NAPAS 247). Hiện tại để null.
- Unique constraint: Không cần UNIQUE(order_id) vì mỗi đơn có thể có nhiều giao dịch (thanh toán 1 phần, refund...).

---

### 3.13. `active_trips` — Trạng thái chuyến đi real-time

```sql
CREATE TABLE active_trips (
    id                  BIGSERIAL       PRIMARY KEY,
    order_id            BIGINT          NOT NULL,
    driver_id           BIGINT          NOT NULL,
    current_stop_id     BIGINT,                         -- Điểm dừng hiện tại (order_stops.id)
    trip_status         VARCHAR(30)     NOT NULL DEFAULT 'assigned'
                        CHECK (trip_status IN (
                            'assigned',           -- Đã gán tài xế
                            'heading_to_pickup',  -- Đang đến điểm lấy
                            'at_pickup',           -- Đã đến điểm lấy
                            'heading_to_dropoff', -- Đang đến điểm giao
                            'at_dropoff',          -- Đã đến điểm giao
                            'completed',          -- Hoàn tất
                            'cancelled'           -- Đã hủy
                        )),
    current_lat         NUMERIC(10,7),
    current_lng         NUMERIC(10,7),
    current_speed_kmh   NUMERIC(5,2),
    current_bearing     SMALLINT,                       -- Hướng di chuyển (0-360 độ)
    eta_next_stop_min   INTEGER,                        -- Số phút đến điểm tiếp theo
    polyline_encoded    TEXT,                           -- Encoded polyline của route hiện tại
    started_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_trips_order              FOREIGN KEY (order_id)  REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT FK_trips_driver             FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    CONSTRAINT UQ_trips_order              UNIQUE (order_id),
    CONSTRAINT CHK_trips_coordinates       CHECK (
        (current_lat IS NULL AND current_lng IS NULL) OR
        (current_lat BETWEEN -90 AND 90 AND current_lng BETWEEN -180 AND 180)
    )
);

CREATE UNIQUE INDEX IX_trips_active_driver ON active_trips (driver_id) WHERE trip_status NOT IN ('completed','cancelled');
```

**Giải thích thiết kế:**
- Bảng này là **bảng trạng thái** (state table) trái ngược với bảng log `gps_tracking`. Mỗi order chỉ có 1 active_trip tại một thời điểm (`UQ_trips_order`).
- `current_lat/lng` được cập nhật real-time khi driver gửi GPS tick. Đây là data được dùng cho Redis cache và WebSocket broadcast.
- `IX_trips_active_driver`: Partial unique index đảm bảo 1 tài xế chỉ chạy 1 chuyến tại 1 thời điểm (không thể nhận đơn mới khi chưa hoàn thành chuyến hiện tại).

---

### 3.14. `gps_tracking` — Lịch sử GPS (TimescaleDB Hypertable)

```sql
-- Tạo bảng với TimescaleDB extension
CREATE TABLE gps_tracking (
    time                TIMESTAMPTZ     NOT NULL,       -- Partition key
    driver_id           BIGINT          NOT NULL,
    trip_id             BIGINT,                         -- FK đến active_trips.id (optional)
    latitude            NUMERIC(10,7)   NOT NULL,
    longitude           NUMERIC(10,7)   NOT NULL,
    altitude_m          SMALLINT,
    speed_kmh           NUMERIC(5,2),
    bearing             SMALLINT,                       -- 0-360 degrees
    accuracy_m          SMALLINT,
    battery_level       SMALLINT,                       -- Pin điện thoại tài xế (%)
    source              VARCHAR(10)     DEFAULT 'gps'
                        CHECK (source IN ('gps', 'network', 'fused')),

    CONSTRAINT FK_gps_driver            FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    CONSTRAINT CHK_gps_lat              CHECK (latitude  BETWEEN -90  AND 90),
    CONSTRAINT CHK_gps_lng              CHECK (longitude BETWEEN -180 AND 180)
);

-- Convert to TimescaleDB hypertable (partition by time, 1 chunk per day)
SELECT create_hypertable('gps_tracking', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX IX_gps_driver_time         ON gps_tracking (driver_id, time DESC);
CREATE INDEX IX_gps_trip_time           ON gps_tracking (trip_id, time DESC) WHERE trip_id IS NOT NULL;

-- Compression policy: nén dữ liệu sau 2 ngày
SELECT add_compression_policy('gps_tracking', INTERVAL '2 days', if_not_exists => TRUE);

-- Retention policy: xóa dữ liệu sau 90 ngày
SELECT add_retention_policy('gps_tracking', INTERVAL '90 days', if_not_exists => TRUE);
```

**Giải thích thiết kế:**
- Đây là bảng **append-only** (chỉ ghi, không sửa/xoá). Mỗi tick GPS là 1 row mới.
- `time` là partition key. Mỗi ngày tạo 1 chunk riêng. Khi query tracking của 1 tài xế trong 24h qua, TimescaleDB tự động prune các chunk ngoài 24h → query cực nhanh.
- `trip_id`: Cho phép trace GPS theo từng chuyến đi để phân tích hành vi tài xế.
- **Compression:** TimescaleDB nén dữ liệu > 2 ngày tuổi với ratio ~90% (từ 100MB còn 10MB).
- **Retention:** Tự động xóa dữ liệu > 90 ngày để tiết kiệm disk (dữ liệu GPS không cần giữ quá lâu vì aggregate từ `orders` và `active_trips` đã đủ cho báo cáo tháng).

---

### 3.15. `eta_predictions` — Kết quả dự báo ETA

```sql
CREATE TABLE eta_predictions (
    id                  BIGSERIAL       PRIMARY KEY,
    order_stop_id       BIGINT,                         -- Dự báo cho điểm dừng nào
    trip_id             BIGINT,                         -- Hoặc cho chuyến đi
    origin_lat          NUMERIC(10,7)   NOT NULL,
    origin_lng          NUMERIC(10,7)   NOT NULL,
    dest_lat            NUMERIC(10,7)   NOT NULL,
    dest_lng            NUMERIC(10,7)   NOT NULL,
    distance_km         NUMERIC(8,2)    NOT NULL,
    predicted_minutes   NUMERIC(6,1)    NOT NULL,
    confidence_low      NUMERIC(6,1),                   -- Khoảng tin cậy dưới (90%)
    confidence_high     NUMERIC(6,1),                   -- Khoảng tin cậy trên (90%)
    actual_minutes      NUMERIC(6,1),                   -- Điền sau khi hoàn thành (để validate model)
    features            JSONB           NOT NULL,       -- {hour, day_of_week, is_rain, traffic_level, ...}
    model_version       VARCHAR(20)     NOT NULL,
    error_minutes       NUMERIC(6,1),                   -- actual - predicted (tính sau)
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_eta_order_stop        FOREIGN KEY (order_stop_id) REFERENCES order_stops(id) ON DELETE SET NULL
);

CREATE INDEX IX_eta_created             ON eta_predictions (created_at DESC);
CREATE INDEX IX_eta_model_version       ON eta_predictions (model_version, created_at DESC);
-- Index để training model: lấy data có actual_minutes để retrain
CREATE INDEX IX_eta_training            ON eta_predictions (model_version, created_at)
                                         WHERE actual_minutes IS NOT NULL;
```

**Giải thích thiết kế:**
- `predicted_minutes`: Output của XGBoost model.
- `actual_minutes`: Điền sau khi tài xế hoàn thành chặng đó. Dùng để tính **MAE (Mean Absolute Error)** của model và có dữ liệu train cho phiên bản model tiếp theo.
- `features` (JSONB): Lưu toàn bộ input features của model tại thời điểm predict. Quan trọng để debug: "Tại sao model predict sai 30 phút?"
- `model_version`: Cho phép A/B test nhiều phiên bản model.

---

### 3.16. `route_optimizations` — Kết quả tối ưu VRP

```sql
CREATE TABLE route_optimizations (
    id                  BIGSERIAL       PRIMARY KEY,
    driver_id           BIGINT          NOT NULL,       -- Tài xế được tối ưu cho
    order_id            BIGINT          NOT NULL,       -- Đơn hàng gốc vừa hoàn thành (trigger)
    suggested_orders    JSONB           NOT NULL DEFAULT '[]',
                                                -- [{order_id, stop_id, lat, lng, weight, detour_km}]
    total_detour_km     NUMERIC(8,2),
    total_extra_earnings NUMERIC(12,0),
    driver_accepted     BOOLEAN,                        -- Tài xế có chấp nhận ghép không?
    driver_responded_at TIMESTAMPTZ,
    solve_time_ms       INTEGER,                        -- Thời gian OR-Tools solve
    solver_params       JSONB           DEFAULT '{}',   -- {max_detour_km:5, max_orders:3, time_window:true}
    status              VARCHAR(20)     NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'accepted', 'rejected', 'expired', 'applied')),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ     NOT NULL,       -- Hết hạn sau 30 giây

    CONSTRAINT FK_routeopt_driver        FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    CONSTRAINT FK_routeopt_order         FOREIGN KEY (order_id)  REFERENCES orders(id) ON DELETE CASCADE
);

CREATE INDEX IX_routeopt_driver_pending  ON route_optimizations (driver_id, status, created_at DESC);
```

**Giải thích thiết kế:**
- `suggested_orders` (JSONB): Lưu các đơn hàng được đề xuất ghép. Không cần tạo bảng phụ vì số lượng đơn ghép nhỏ (1-3).
- `solve_time_ms`: Ghi lại thời gian chạy OR-Tools để monitor performance.
- `expires_at`: Đề xuất chỉ có hiệu lực 30 giây. Nếu tài xế không phản hồi → expired.

---

### 3.17. `notifications` — Lịch sử thông báo

```sql
CREATE TABLE notifications (
    id                  BIGSERIAL       PRIMARY KEY,
    user_id             BIGINT          NOT NULL,
    title               VARCHAR(200)    NOT NULL,
    body                TEXT            NOT NULL,
    notification_type   VARCHAR(30)     NOT NULL
                        CHECK (notification_type IN (
                            'new_order', 'bid_accepted', 'order_cancelled',
                            'driver_arrived', 'order_delivered', 'payment_received',
                            'document_expiring', 'promotion', 'system'
                        )),
    reference_type      VARCHAR(30),                    -- 'order', 'payment', 'document'
    reference_id        BIGINT,                         -- ID của đối tượng liên quan
    is_read             BOOLEAN         NOT NULL DEFAULT FALSE,
    is_pushed           BOOLEAN         NOT NULL DEFAULT FALSE,
    push_provider       VARCHAR(20)     DEFAULT 'fcm',
    push_response       JSONB,                          -- Response từ FCM (debug)
    read_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_notifications_user    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IX_notifications_user_unread ON notifications (user_id, created_at DESC) WHERE is_read = FALSE;
CREATE INDEX IX_notifications_user_all    ON notifications (user_id, created_at DESC);
```

---

## 4. SƠ ĐỒ QUAN HỆ (RELATIONSHIP DIAGRAM)

```
users 1──────1 drivers 1──────N driver_documents
  │              │
  │              │ 1──────1 vehicles
  │              │
  │              │ 1──────N active_trips
  │              │              │
  │ 1──────N orders─────────────┘
  │              │ 1──────N order_stops
  │              │               │
  │              │ 1──────N order_items
  │              │
  │              │ 1──────1 payments (có thể nhiều payment cho 1 order)
  │              │
  │              │ 1──────N eta_predictions
  │              │
  │              │ 1──────N route_optimizations
  │              │
  │ 1──────N notifications
  │
  │ 1──────1 businesses ────N business_contracts
  │              │
  │              └──────N business_drivers ────N drivers
```

**Ghi chú:**
- `users (1) ── (1) drivers`: Mỗi user có 0 hoặc 1 hồ sơ tài xế (tài xế là 1 subtype của user).
- `drivers (1) ── (N) driver_documents`: Mỗi tài xế có thể upload nhiều loại giấy tờ khác nhau.
- `orders (1) ── (N) order_stops`: 1 đơn hàng có nhiều điểm dừng (tối thiểu 2: pickup + dropoff).
- `orders (1) ── (N) payments`: 1 đơn có thể có nhiều giao dịch (thanh toán, hoàn tiền 1 phần).

---

## 5. AUDIT LOG & EVENT SOURCING

### 5.1. `order_status_logs` — Audit trail thay đổi trạng thái đơn hàng

```sql
CREATE TABLE order_status_logs (
    id                  BIGSERIAL       PRIMARY KEY,
    order_id            BIGINT          NOT NULL,
    from_status         VARCHAR(30),
    to_status           VARCHAR(30)     NOT NULL,
    changed_by          BIGINT,                         -- user_id người thực hiện
    change_reason       TEXT,
    metadata            JSONB           DEFAULT '{}',
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT FK_statuslogs_order       FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE INDEX IX_statuslogs_order          ON order_status_logs (order_id, created_at DESC);
```

---

## 6. CHIẾN LƯỢC MIGRATION & SEED DATA

### 6.1. Cấu trúc thư mục migrations

```
leopard-backend/
├── migrations/
│   ├── versions/
│   │   ├── 001_initial_users_and_auth.py
│   │   ├── 002_drivers_vehicles_documents.py
│   │   ├── 003_orders_core_tables.py
│   │   ├── 004_business_contracts_and_fleet.py
│   │   ├── 005_gps_tracking_and_timescaledb.py
│   │   ├── 006_payments_and_vietqr.py
│   │   ├── 007_eta_and_vrp_tables.py
│   │   └── 008_notifications_and_audit_log.py
│   └── alembic.ini
├── scripts/
│   ├── seed_users.py
│   ├── seed_orders_mock.py
│   ├── seed_gps_tracking.py
│   └── seed_eta_training_data.py
```

### 6.2. Seed data tối thiểu cho phát triển

```sql
-- 1. Admin user
INSERT INTO users (firebase_uid, role, phone, full_name, is_verified)
VALUES ('admin_firebase_uid', 'admin', '0900000000', 'Admin Leopard', TRUE);

-- 2. Sample driver
INSERT INTO users (firebase_uid, role, phone, full_name, is_verified)
VALUES ('driver_firebase_1', 'driver', '0901111111', 'Nguyễn Văn Tài', TRUE);
-- ... insert vào drivers, vehicles

-- 3. Sample shipper
INSERT INTO users (firebase_uid, role, phone, full_name, is_verified)
VALUES ('shipper_firebase_1', 'shipper', '0902222222', 'Công ty VLXD Nam Phát', TRUE);
```

---

## 7. TRIGGER VÀ FUNCTION (BUSINESS LOGIC Ở DB LAYER)

### 7.1. Auto-update `updated_at` trigger

```sql
-- Generic trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_drivers_updated_at
    BEFORE UPDATE ON drivers FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_orders_updated_at
    BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_timestamp();
-- ... và các bảng khác
```

### 7.2. Log status change trigger

```sql
-- Tự động ghi log khi order.status thay đổi
CREATE OR REPLACE FUNCTION log_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO order_status_logs (order_id, from_status, to_status, metadata)
        VALUES (NEW.id, OLD.status, NEW.status,
                jsonb_build_object('changed_by', current_setting('app.current_user_id', TRUE)));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_orders_status_change
    AFTER UPDATE OF status ON orders
    FOR EACH ROW EXECUTE FUNCTION log_order_status_change();
```

### 7.3. Validate trip driver availability

```sql
-- Đảm bảo tài xế không được gán đơn khi đang có trip active
CREATE OR REPLACE FUNCTION validate_driver_availability()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM active_trips
        WHERE driver_id = NEW.driver_id
          AND trip_status NOT IN ('completed', 'cancelled')
          AND id <> COALESCE(NEW.id, 0)
    ) THEN
        RAISE EXCEPTION 'Driver % already has an active trip', NEW.driver_id
            USING HINT = 'Complete or cancel current trip first';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_active_trips_driver_check
    AFTER INSERT OR UPDATE OF driver_id ON orders
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW WHEN (NEW.driver_id IS NOT NULL)
    EXECUTE FUNCTION validate_driver_availability();
```

---

## 8. CHIẾN LƯỢC BACKUP & DISASTER RECOVERY

| Hạng mục | Chi tiết |
|---|---|
| **Full backup** | `pg_dump` toàn bộ DB mỗi ngày lúc 2:00 AM (cron job) |
| **WAL archiving** | Bật `archive_mode = on` để point-in-time recovery (PITR) |
| **Backup storage** | Lưu file `.dump` lên Google Drive hoặc S3-compatible (rclone) |
| **Retention** | Giữ 7 ngày backup gần nhất, 30 ngày cho WAL archives |
| **Recovery drill** | Test restore 1 lần trước khi bảo vệ đồ án |

---

## 9. REDIS CACHE DESIGN (BỔ SUNG)

| Key Pattern | Type | TTL | Purpose |
|---|---|---|---|
| `driver:loc:{driver_id}` | String `{"lat":10.7,"lng":106.6,"ts":123456}` | 30s | Current driver location cache |
| `driver:geohash:{geohash}` | Set of driver_ids | N/A | Spatial index cho tìm tài xế gần |
| `route:{from_lat}:{from_lng}:{to_lat}:{to_lng}` | String (JSON polyline) | 24h | Cache Vietmap routing results |
| `order:quote:{shipper_id}:{fingerprint}` | String `{price, eta}` | 5min | Cache báo giá tránh gọi lại |
| `order:{id}:tracking` | String `{lat, lng, eta, status}` | 5min | Cache tracking data cho Web UI |
| `rate_limit:{ip}:{endpoint}` | Integer (counter) | 60s | Token bucket for rate limiting |
| `session:{token_hash}` | String `{user_id, role}` | 24h | Session cache |
| `vietmap:route:{hash}` | String (encoded polyline) | 24h | Cache Vietmap API calls |
| `notif:pending:{user_id}` | List | — | Queue pending push notifications |

---

## 10. KIỂM TRA & VALIDATION

| # | Kiểm tra | Phương pháp | Kỳ vọng |
|---|---|---|---|
| 1 | Kiểm tra tất cả FK references | `EXPLAIN ANALYZE` trên JOIN queries | Không sequential scan trên FK columns |
| 2 | Kiểm tra unique constraints | INSERT duplicate giá trị | Báo lỗi unique violation |
| 3 | Kiểm tra check constraints | INSERT giá trị vi phạm (rating < 0) | Báo lỗi check violation |
| 4 | Kiểm tra partial index | Query với WHERE clause matching index | Index scan, không sequential scan |
| 5 | Kiểm tra TimescaleDB compression | Kiểm tra compression ratio | Tỉ lệ nén ≥ 80% |
| 6 | Kiểm tra Redis cache hit | Start server, query 100 lần | Hit rate ≥ 85% trong 5 phút |
