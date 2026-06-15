# ADR-004: Thiết kế Kiến trúc Cơ sở Dữ liệu & Caching

| Field | Value |
|---|---|
| **ID** | ADR-004 |
| **Tiêu đề** | Thiết kế Kiến trúc Cơ sở Dữ liệu & Caching |
| **Ngày** | 2026-06-15 |
| **Trạng thái** | Approved |
| **Tác giả** | Tech Lead Team LEOPARD |
| **Stakeholders** | Product Owner, Dev Team, DBA |
| **Phiên bản** | 1.0 |

---

## 1. BỐI CẢNH (Context)

Hệ thống LEOPARD có các đặc điểm dữ liệu phức tạp, require một kiến trúc lưu trữ có chiến lược:

### Đặc điểm workload của hệ thống
1. **ACID Transactions nghiêm ngặt:** Tạo đơn hàng, nhận thanh toán, khóa tài khoản khuyến mại. Không được phép có trạng thái sai lệch (double spending, đơn bị mất giữa chừng).
2. **Dữ liệu không gian (Spatial/GIS):** Cần lưu trữ và truy vấn tọa độ GPS tài xế (Point), lưu tuyến đường (LineString), tìm tài xế gần nhất trong bán kính N km.
3. **Time-series dữ liệu tốc độ cao:** Mỗi tài xế gửi vị trí GPS mỗi 3-5 giây. Với 100 tài xế online đồng thời, mỗi ngày có thể sinh 500K - 1M bản ghi location. Cần lưu để tracking lịch sử, tính ETA, và audit.
4. **Document/Flexible Schema:** Một số entity như `Order` có cấu trúc linh hoạt (danh sách điểm dừng biến động, metadata hàng hóa, yêu cầu đặc biệt). JSON/JSONB tốt hơn là tạo 10 bảng phụ.
5. **Read-after-write consistency:** Khi user tạo đơn, họ phải thấy đơn của mình xuất hiện ngay lập tức trong danh sách.
6. **Caching cho dữ liệu nóng:** Dữ liệu định tuyến (route), báo giá, vị trí hiện tại của tài xế cần được cache để giảm tải DB.

### Ràng buộc
- Ngân sách hạn hẹp (không thể dùng nhiều dịch vụ managed).
- Có thể deploy trên 1 VPS duy nhất giai đoạn prototype.
- Team sinh viên cần công nghệ dễ học, cộng đồng lớn.

---

## 2. CÁC PHƯƠNG ÁN ĐÃ XEM XÉT (Alternatives Considered)

### Phương án A: PostgreSQL (Primary OLTP + PostGIS + TimescaleDB) + Redis (Caching & Queue) — Recommended

**PostgreSQL là database chính** đảm nhiệm tất cả các công việc nhờ hệ sinh thái extension mở rộng:
- **PostGIS**: Extension cho spatial query (tìm tài xế gần nhất, vẽ vùng phủ sóng).
- **TimescaleDB**: Hypertable cho time-series data (GPS tracking points) giúp tự động partition theo thời gian và nén dữ liệu cũ.
- **JSONB**: Cho phép lưu schema linh hoạt như Order metadata, không cần tạo 10 bảng như MySQL.

| Tiêu chí | Đánh giá |
|---|---|
| **ACID** | Đầy đủ, hỗ trợ Serializable Isolation cho giao dịch thanh toán |
| **Spatial Query** | PostGIS — giải pháp spatial số 1 thế giới, hỗ trợ `ST_DWithin`, `ST_DistanceSphere`, `KNN GiST index`, hàng trăm hàm xử lý không gian. Google, Uber, Zillow đều dùng |
| **Time-Series** | TimescaleDB hiệu quả gấp 20x so với PostgreSQL thuần cho time-series (nhờ hypertable, auto partitioning, compression 90%+) |
| **Flexible Schema** | JSONB hỗ trợ GIN index, query `@>`, `?` operators, mạnh hơn MySQL JSON |
| **Performance** | Dùng `EXPLAIN ANALYZE` tuning query plan, hỗ trợ Parallel Query Execution |
| **Migrations** | Alembic + SQLAlchemy quản lý schema thay đổi theo phiên bản (version controlled) |
| **Chi phí** | Miễn phí, open-source, chạy trên VPS thấp nhất (512MB RAM vẫn chạy tốt 50 concurrent connections) |
| **AI Agent support** | PostgreSQL là DB được AI Agent hỗ trợ viết query tốt nhất (SQL chuẩn, rõ ràng) |

**Redis làm layer cache & message queue:**
- **Cache:** Lưu location hiện tại của tài xế (key `driver:location:<driver_id>`, value `{lat, lng, ts}`, EVAL script để tìm tài xế gần nhất theo geohash). Giảm tải spatial query lên PostGIS cho mỗi request.
- **Pub/Sub:** WebSocket broadcast location từ backend worker này sang worker khác (horizontal scaling).
- **Rate Limiting:** Chống spam API (token bucket algorithm).
- **Celery Broker:** Message broker cho Celery xử lý VRP tasks không đồng bộ.

### Phương án B: MongoDB (Primary DB) + TimescaleDB (Time-series)

| Tiêu chí | Đánh giá |
|---|---|
| **Flexible Schema** | Rất mạnh — Document model native, không cần JSONB |
| **Spatial Query** | Có hỗ trợ `2dsphere` index, nhưng số lượng hàm spatial ít hơn PostGIS rất nhiều |
| **ACID** | Multi-document ACID từ version 4.0, nhưng performance giảm mạnh với các operation phức tạp |
| **Time-Series** | Không hỗ trợ native, phải dùng thêm TimescaleDB hoặc InfluxDB → Tăng complexity (2 database engine khác nhau để maintain) |
| **Query Complexity** | Aggregation pipeline khó debug và viết hơn SQL với complex JOIN |
| **Transactions** | MongoDB distributed transactions kém ổn định hơn PostgreSQL trên VPS single-node |
| **Rủi ro** | MongoDB trên VPS nhỏ tốn RAM rất nhiều (WiredTiger cache ít nhất 256MB), dễ gây OOM Kill trên VPS 1-2GB RAM |

### Phương án C: MySQL 8 (Primary DB)

| Tiêu chí | Đánh giá |
|---|---|
| **Spatial Query** | MySQL 8 có hỗ trợ SRID, `ST_Distance_Sphere`, nhưng feature set spatial chỉ bằng 30% PostGIS |
| **Time-Series** | Không có, phải tự roll partition table bằng tay (mất công) |
| **JSON Support** | Có JSON column type nhưng GIN index yếu hơn PostgreSQL JSONB, không có partial index update |
| **Connection Pool** | Không có `LISTEN/NOTIFY` cho real-time events, phải polling |
| **Kết luận** | MySQL thua PostgreSQL ở mọi tiêu chí của hệ thống này. Không có lý do để chọn |

---

## 3. QUYẾT ĐỊNH (Decision)

> **Chọn PostgreSQL 16 với các extension PostGIS + TimescaleDB làm Primary Database, và Redis 7 làm Cache & Message Broker.**
>
> Kiến trúc Single-DB, Multi-Extension: Tận dụng sức mạnh của PostgreSQL ecosystem để giải quyết đồng thời 3 bài toán (OLTP, Spatial, Time-Series) trong MỘT engine duy nhất — không cần maintain 3 database engine khác nhau.

### ERD Quan hệ cốt lõi (Logical Level)

```
┌──────────────┐       ┌────────────────────┐       ┌──────────────────┐
│    users     │       │      orders        │       │     drivers      │
├──────────────┤       ├────────────────────┤       ├──────────────────┤
│ id (PK)      │──┐    │ id (PK)            │    ┌──│ id (PK)          │
│ firebase_uid │  │    │ shipper_id (FK)>───┼───┐│  │ user_id (FK)     │
│ full_name    │  │    │ driver_id (FK) ────┼───┼┼──│ vehicle_id (FK)  │
│ phone        │  │    │ status (enum)      │   ││  │ license_number   │
│ email        │  │    │ total_price        │   ││  │ is_available     │
│ avatar_url   │  │    │ payment_method     │   ││  │ current_location │
│ role (enum)  │  │    │ payment_status     │   ││  │ rating           │
│ created_at   │  │    │ notes              │   ││  └──────────────────┘
└──────────────┘  │    │ created_at         │   ││
                  │    └────────┬───────────┘   ││
                  │             │               ││
┌──────────────┐  │    ┌───────▼──────────┐     ││  ┌──────────────────┐
│  businesses  │  │    │   order_stops    │     ││  │    vehicles      │
├──────────────┤  │    ├─────────────────┤     ││  ├──────────────────┤
│ id (PK)      │  │    │ id (PK)         │     ││  │ id (PK)          │
│ owner_id (FK)│──┘    │ order_id (FK)───┼─────┘│  │ driver_id (FK)───┼──┘
│ company_name │       │ type (pickup/    │      │  │ plate_number     │
│ tax_code     │       │   dropoff/mid)   │      │  │ vehicle_type     │
│ fleet_size   │       │ address (jsonb)  │      │  │ max_weight_kg    │
│ contract_tier│       │ contact_phone    │      │  │ max_height_m     │
└──────────────┘       │ latitude         │      │  │ max_width_m      │
                       │ longitude        │      │  │ max_length_m     │
┌──────────────┐       │ sequence_order   │      │  └──────────────────┘
│   payments   │       └─────────────────┘      │
├──────────────┤                                  │  ┌──────────────────┐
│ id (PK)      │       ┌─────────────────┐        │  │driver_documents  │
│ order_id(FK)─┼───────│  order_items    │        │  ├──────────────────┤
│ amount       │       ├─────────────────┤        └──│ driver_id (FK)   │
│ method       │       │ id (PK)         │           │ doc_type (enum)  │
│ status       │       │ order_id (FK)───┼───────────│ doc_url          │
│ bank_txn_id  │       │ description     │           │ verified         │
│ qr_code_url  │       │ weight_kg       │           └──────────────────┘
└──────────────┘       │ quantity        │
                       │ image_urls(jsonb│
┌───────────────────┐  │ special_reqs    │
│ gps_tracking      │  └─────────────────┘
│ (TimescaleDB      │
│ Hypertable)       │  ┌──────────────────────┐
├───────────────────┤  │  business_contracts  │
│ time (partition)  │  ├──────────────────────┤
│ driver_id (FK)    │  │ id (PK)              │
│ latitude          │  │ business_id (FK)─────┼───┐
│ longitude         │  │ contract_type        │   │
│ speed_kmh         │  │ start_date           │   │
│ bearing           │  │ end_date             │   │
│ accuracy_m        │  │ monthly_fee          │   │
└───────────────────┘  │ discount_rate        │   │
                       └──────────────────────┘   │
                                                  │
┌──────────────────────┐                          │
│     eta_predictions  │                          │
├──────────────────────┤                          │
│ id (PK)              │                          │
│ order_stop_id (FK)   │                          │
│ predicted_minutes    │                          │
│ confidence_low       │                          │
│ confidence_high      │                          │
│ features (jsonb)     │  (traffic, weather...)   │
│ predicted_at         │                          │
└──────────────────────┘                          │
                                                  │
┌──────────────────────────────┐                  │
│ route_optimizations         │                  │
├──────────────────────────────┤                  │
│ id (PK)                      │                  │
│ batch_token                  │                  │
│ input_orders (jsonb)         │                  │
│ input_drivers (jsonb)        │                  │
│ output_assignments (jsonb)   │                  │
│ total_cost_km                │                  │
│ utilization_rate             │                  │
│ solve_time_ms                │                  │
│ created_at                   │                  │
└──────────────────────────────┘                  │
                                                  │
┌──────────────────────────────────────────────────┴─┐
│ active_trips (quasi-cache table)                    │
├────────────────────────────────────────────────────┤
│ id (PK)                                             │
│ order_id (FK) ─────────────────────────────────┐   │
│ driver_id (FK)                                  │   │
│ trip_status (assigned/pickup/in_transit/delivered)   │
│ polyline_encoded (TEXT)                          │   │
│ current_lat                                       │   │
│ current_lng                                       │   │
│ eta_next_stop_minutes                             │   │
│ started_at                                        │   │
│ updated_at (auto-update trigger)                  │   │
└────────────────────────────────────────────────────┘   │
```

### Chiến lược phân vùng (Partitioning) cho GPS Tracking

`gps_tracking` table sử dụng TimescaleDB Hypertable:
- **Partition key:** `time` (mỗi partition = 1 ngày dữ liệu).
- **Compression policy:** Nén dữ liệu > 2 ngày tuổi (tiết kiệm 90% disk).
- **Retention policy:** Xóa dữ liệu > 90 ngày (giữ lại dữ liệu cho audit, nhưng không tốn storage).
- **Query pattern:** `SELECT * FROM gps_tracking WHERE driver_id = $1 AND time > NOW() - INTERVAL '24 hours' ORDER BY time DESC`
  - TimescaleDB sẽ tự động prune các partition ngoài 24h, chỉ scan 1-2 chunk = query nhanh hơn 100x so với table không có partition.

### Chiến lược Redis Cache

| Cache Key Pattern | Kiểu dữ liệu | TTL | Mục đích |
|---|---|---|---|
| `driver:location:{driver_id}` | String (JSON `{lat,lng,ts}`) | 30s | Vị trí hiện tại, dùng cho tìm tài xế gần mà không cần query PostGIS |
| `driver:geohash:{geohash}` | Set (danh sách driver_id) | Live (ZADD update liên tục) | Index không gian trên Redis để tìm nhanh tài xế trong vùng |
| `route:{origin_lat}:{origin_lng}:{dest_lat}:{dest_lng}:{profile}` | String (JSON polyline) | 24h | Cache kết quả định tuyến OSRM (tránh gọi lại cho route giống hệt) |
| `order:quote:{user_id}:{fingerprint}` | String (JSON giá) | 5 phút | Cache kết quả báo giá để tránh tính toán lại khi user refresh |
| `rate_limit:{ip}:{endpoint}` | Integer (counter) | 60s | Rate limiting |
| `session:{token_hash}` | String (JSON user data) | 24h | JWT session cache, kiểm tra nhanh user state |

### Chiến lược Index cho PostgreSQL

| Bảng | Index | Kiểu | Mục đích |
|---|---|---|---|
| `orders` | `IX_orders_shipper_id_status` | B-tree (`shipper_id`, `status`) | Query lịch sử đơn của shipper |
| `orders` | `IX_orders_driver_id_status` | B-tree (`driver_id`, `status`) | Query danh sách đơn của tài xế |
| `orders` | `IX_orders_created_at` | B-tree (`created_at`) | Filter theo ngày, dashboard |
| `drivers` | `IX_drivers_current_location` | GiST (geometry) | KNN search tìm tài xế gần |
| `drivers` | `IX_drivers_vehicle_type_available` | B-tree (`vehicle_type`, `is_available`) | Lọc tài xế theo loại xe |
| `order_stops` | `IX_order_stops_lat_lng` | GiST (geometry) | Tìm điểm giao/nhận gần |
| `gps_tracking` | `IX_gps_driver_time` | B-tree (`driver_id`, `time DESC`) | Query lịch sử location |
| `payments` | `IX_payments_order_id` | B-tree (`order_id`) | Tra cứu payment của đơn |
| `business_contracts` | `IX_contracts_business_active` | Partial index (`business_id`) WHERE `end_date > NOW()` | Tìm hợp đồng active |

---

## 4. HỆ QUẢ (Consequences)

### ✅ Tích cực (Positive)
1. **Single engine, 3 use cases:** PostgreSQL + PostGIS + TimescaleDB giải quyết toàn bộ nhu cầu trong 1 engine: giao dịch OLTP, spatial query phức tạp, và time-series hiệu quả cao.
2. **Community cực lớn:** PostgreSQL có tài liệu tiếng Việt, cộng đồng mạnh (Vietnam PostgreSQL User Group), Stack Overflow answer đầy đủ.
3. **AI Agent hỗ trợ tốt:** SQL là ngôn ngữ AI Agent hiểu sâu nhất, có thể sinh query phức tạp (CTE, window functions, PostGIS spatial) chính xác.
4. **Tiết kiệm chi phí:** Không cần mua thêm MongoDB Atlas hay InfluxDB Cloud managed service.
5. **Dễ backup & restore:** Chỉ cần `pg_dump` và `pg_restore` 1 lệnh cho toàn bộ data.

### ⚠️ Trung tính (Neutral)
1. PostgreSQL config tuning ban đầu cần setup các thông số (`shared_buffers`, `work_mem`, `effective_cache_size`) phù hợp với VPS RAM size.
2. TimescaleDB là extension code-open nhưng có một số tính năng nâng cao (compression automated, continuous aggregates) yêu cầu TimescaleDB Community license.

### ❌ Tiêu cực (Negative)

| Rủi ro | Impact | Mitigation |
|---|---|---|
| **VPS RAM giới hạn**, PostgreSQL + Redis trên cùng 1 máy có thể cạnh tranh memory | Cao (OOM Kill) | Đặt memory limit cho Redis (`maxmemory 256mb`) và PostgreSQL (`shared_buffers=128MB`), tổng không vượt 70% VPS RAM |
| **Spatial query chậm** nếu Redis cache miss | Trung bình | Sử dụng Redis Geo index (`GEOADD` + `GEOSEARCH`) làm cache layer đầu tiên, chỉ fallback PostGIS khi cache miss |
| **TimescaleDB learning curve** | Thấp | Cú pháp TimescaleDB giống hệt PostgreSQL SQL, chỉ thêm vài function (`create_hypertable()`, `add_compression_policy()`) |

---

## 5. ĐIỀU KIỆN KIỂM TRA (Validation Criteria)

| # | Tiêu chí | Phương pháp kiểm tra | Ngưỡng chấp nhận |
|---|---|---|---|
| 1 | Tìm 10 tài xế gần nhất trong bán kính 5km | Query PostGIS `ST_DWithin` với 500 drivers mock data | Response < 50ms |
| 2 | Ghi location tracking 200 drivers mỗi 3s | Insert vào TimescaleDB hypertable concurrent | Throughput ≥ 600 inserts/s, không drop |
| 3 | Nén dữ liệu GPS tracking | Kiểm tra compression ratio sau khi enable TimescaleDB compression policy | Ratio ≥ 80% disk saved |
| 4 | Transaction integrity | 20 requests đặt đơn + thanh toán đồng thời | 0 trường hợp trùng lặp hoặc mất dữ liệu |
| 5 | Redis cache hit rate | Monitor Redis INFO stats sau 1 giờ load test | Hit rate ≥ 85% |
| 6 | Query lịch sử đơn hàng của user | EXPLAIN ANALYZE query lấy 50 orders mới nhất | Index scan, không sequential scan. Time < 10ms |

---

## 6. THAM KHẢO (References)

- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/16/)
- [PostGIS Manual](https://postgis.net/docs/manual-3.4/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Redis Geo Commands](https://redis.io/commands/?group=geo)
- [SQLAlchemy 2.0 Async PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)

---

## 7. LỊCH SỬ THAY ĐỔI (Changelog)

| Phiên bản | Ngày | Tác giả | Mô tả |
|---|---|---|---|
| 1.0 | 2026-06-15 | Tech Lead | Bản đầu tiên, quyết định PostgreSQL + PostGIS + TimescaleDB + Redis |
