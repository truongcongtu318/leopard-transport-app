# ADR-005: Kiến trúc Mô hình Dự báo ETA và Tối ưu Vận trù học VRP

| Field | Value |
|---|---|
| **ID** | ADR-005 |
| **Tiêu đề** | Kiến trúc Mô hình Dự báo ETA và Tối ưu Vận trù học VRP |
| **Ngày** | 2026-06-15 |
| **Trạng thái** | Approved |
| **Tác giả** | Tech Lead Team LEOPARD |
| **Stakeholders** | Product Owner, AI Engineer, Data Engineer, Dev Team |
| **Phiên bản** | 1.0 |

---

## 1. BỐI CẢNH (Context)

Đây là hai module "xương sống" tạo nên lợi thế cạnh tranh cốt lõi của LEOPARD so với các app vận tải hàng hóa truyền thống (gọi xe tải qua điện thoại, báo giá thủ công).

### 1.1. ETA Prediction (Dự báo thời gian di chuyển)
**Yêu cầu:** Khi shipper đặt đơn, hệ thống cần dự báo **ETD (Estimated Time of Departure)** và **ETA (Estimated Time of Arrival)** chính xác tới từng phút cho mỗi chặng:

- XE đến điểm lấy hàng lúc mấy giờ?
- XE chạy từ điểm A tới điểm B mất bao lâu, dựa trên **điều kiện giao thông real-time và thời tiết hiện tại**?

**Vấn đề:**
- Các app thông thường dùng đường chim bay (Haversine) / tốc độ trung bình (giả sử 30km/h) → Sai số lên tới 30-50 phút trong giờ cao điểm.
- Cần một mô hình Machine Learning được huấn luyện để dự báo chính xác hơn dựa trên các đặc trưng có ảnh hưởng: giờ trong ngày, ngày trong tuần, khoảng cách, loại xe, thời tiết, và dữ liệu traffic.

### 1.2. VRP – Vehicle Routing Problem (Tối ưu ghép hàng & tuyến đường)
**Yêu cầu:** Sau khi tài xế hoàn thành một cuốc xe giao hàng từ kho về quận Bình Thạnh, thay vì chạy rỗng về kho (mất tiền xăng, lãng phí thời gian), hệ thống có thể đề xuất ghép thêm 1-2 đơn hàng trong cùng khu vực đang chờ gửi đi hoặc chuyển đi nơi khác để tận dụng tải xe chiều về.

**Vấn đề:**
- Đây là bài toán NP-Hard (tối ưu tổ hợp), không thể giải bằng brute force với > 10 điểm.
- Google OR-Tools solver cung cấp thuật toán Heuristic cho VRP nhưng cần cấu hình chính xác về:
  - **Capacity Constraint:** Tổng trọng lượng hàng hóa ≤ sức chở xe.
  - **Time Window Constraint:** Mỗi điểm giao/nhận có khung giờ (VD: 9h - 11h sáng).
  - **Driver Break Constraint:** Tài xế có giờ nghỉ bắt buộc theo luật.
  - **Max Route Distance:** Quãng đường tối đa mỗi tài xế có thể đi trong ca làm việc.

---

## 2. CÁC PHƯƠNG ÁN ĐÃ XEM XÉT (Alternatives Considered)

### 2.1. ETA Prediction — Các phương án

#### Phương án A: XGBoost Regressor (Supervised Learning) — Recommended

| Tiêu chí | Đánh giá |
|---|---|
| **Độ chính xác** | Rất cao — XGBoost thường đạt kết quả tốt nhất trên các bài toán regression có features hỗn hợp (số + category) |
| **Interpretability** | SHAP values có thể giải thích tại sao ETA dự báo dài hơn bình thường (VD: "Vì giờ cao điểm buổi sáng + mưa nhẹ") |
| **Training Speed** | Nhanh (GPU acceleration optional), phù hợp retrain theo định kỳ |
| **Inference Latency** | Cực kỳ nhanh (~1ms / prediction) — có thể chạy real-time |
| **Data Requirement** | Cần labeled data: `features → actual travel_time`. Trong giai đoạn đầu có thể sinh mock data từ OSRM + mô phỏng traffic |
| **Scalability** | Chạy được trên CPU mà không cần GPU, phù hợp VPS giá rẻ |

#### Phương án B: Deep Learning (LSTM/Transformer)

| Tiêu chí | Đánh giá |
|---|---|
| **Độ chính xác** | Tương đương XGBoost cho bài toán time-series ngắn (1-2h), cao hơn với dự báo cực dài |
| **Training resources** | Cần GPU để train (tốn tiền), inference có thể trên CPU nhưng chậm hơn |
| **Model size** | Lớn (~100-500MB), tốn RAM và disk VPS |
| **Data Requirement** | Cần nhiều dữ liệu lịch sử (hàng triệu samples) để generalize tốt — không phù hợp với Phase 1 |
| **Complexity** | Khó debug, khó giải thích (black box) → Giám khảo đồ án có thể đánh giá thấp vì không hiểu logic |

#### Phương án C: Naive Baseline (Tốc độ trung bình + distance)

| Tiêu chí | Đánh giá |
|---|---|
| **Độ chính xác** | Kém (MAPE ~40-60%), không phản ánh traffic thực tế |
| **Phù hợp** | Chỉ làm baseline để so sánh với model AI trong báo cáo tốt nghiệp |

---

### 2.2. VRP Optimization — Các phương án

#### Phương án A: Google OR-Tools (CP-SAT + Greedy Heuristic) — Recommended

| Tiêu chí | Đánh giá |
|---|---|
| **Độ phức tạp giải bài toán** | Có thể giải VRP đến **200 địa điểm, 50 tài xế** trong vòng < 30s (hơn 10^50 tổ hợp nếu brute force) |
| **Ràng buộc được hỗ trợ** | Capacity, Time Window, Drivetime limit, Distance limit, Pickup & Dropoff pairing, Depot, Fixed cost |
| **License** | Apache 2.0 (hoàn toàn miễn phí cho cả thương mại) |
| **Python support** | `ortools` package chính thức, PyPI install trong 1 lệnh |
| **Latency** | Không phải real-time (mất vài giây đến vài phút) → Chạy background qua Celery Task |
| **AI Agent code** | Google OR-Tools có syntax rõ ràng, nhiều ví dụ mẫu, AI Agent sinh code chính xác |

#### Phương án B: PyVRP (Miễn phí, C++ native)

| Tiêu chí | Đánh giá |
|---|---|
| **Performance** | Có thể nhanh hơn OR-Tools trong một số bài toán VRP |
| **Cộng đồng** | Nhỏ hơn nhiều so với OR-Tools, tài liệu hạn chế |
| **Documentation** | Văn bản kỹ thuật đầy đủ hơn cho người mới bắt đầu |
| **Kết luận** | Hợp lệ, nhưng OR-Tools có cộng đồng lớn hơn và AI Agent hỗ trợ tốt hơn |

#### Phương án C: OptaPlanner (Java)

| Tiêu chí | Đánh giá |
|---|---|
| **Ecosystem** | Rất mạnh (Red Hat maintain), hỗ trợ Constraint Streams |
| **Rủi ro** | Java + Quarkus runtime → Không phù hợp với stack Python (phải mở REST endpoint riêng) |
| **Kết luận** | Quá phức tạp cho dự án này |

---

## 3. QUYẾT ĐỊNH (Decision)

> **1. ETA Prediction: Chọn XGBoost Regressor (Phương án A)**
> 2. **VRP Optimization: Chọn Google OR-Tools (Phương án A)**
> 
> Cả hai module đều chạy trong Python ecosystem, tương thích với ADR-002 (Backend FastAPI). Đảm bảo tính thống nhất và dễ bảo trì cùng nhau.

### 3.1. ETA Prediction — Kiến trúc chi tiết

#### Feature Engineering Pipeline

```
Input Request:
  origin_lat, origin_lng
  dest_lat, dest_lng
  vehicle_type (xe tải nhỏ/trung/lớn)
  pickup_datetime (timestamp)

OSRM API ──> distance_km, total_seconds (không traffic)
             elevation_gain_m
             urban_distance_ratio (tỷ lệ đường trong nội đô)

Feature Engineering Layer:
  hour_of_day          (0-23)     → one-hot [0,0,0,1,...,0,0,0]
  day_of_week          (0-6)      → one-hot [0,1,0,0,0,0,0]
  is_holiday           (0/1)      → tra cứu lịch nghỉ lễ Việt Nam
  is_weekend           (0/1)
  is_rush_hour         (0/1)      → sáng 7-9h, chiều 17-19h
  is_rain              (0/1)      → OpenWeather API
  distance_km          (float)
  urban_ratio          (0-1)      → tỷ lệ đường trong đô thị
  speed_bucket         (int)      → tốc độ trung bình gần đây cho route này
  historical_travel_time_minutes (float) → nếu route đã chạy trước đó
```

#### Model Architecture

```python
import xgboost as xgb

model = xgb.XGBRegressor(
    n_estimators=500,           # 500 trees
    max_depth=8,                # depth of tree
    learning_rate=0.05,         # epsilon
    subsample=0.8,              # sampling for variance reduction
    colsample_bytree=0.7,       # feature sampling
    reg_alpha=0.1,              # L1 regularization
    reg_lambda=1,               # L2 regularization
    random_state=42,
    early_stopping_rounds=20,   # stop before overfit
    eval_metric=["mae", "mape"],
)

# Training data: 80,000 samples (mock + synthetic)
# Test data: 20,000 samples
# Feature dimension: 25 features
```

#### Training Data Strategy

**Phase 1 (Mock — Dùng cho demo tốt nghiệp):**
Sinh dữ liệu tổng hợp bằng Python script:
1. Random route từ OSRM (lấy distance OSRM chính xác).
2. Thêm noise Gaussian vào travel_time dựa trên:
   - Giờ cao điểm: noise +20% đến +80% travel time gốc.
   - Mưa: noise +10% đến +40%.
   - Loại xe: xe tải chậm hơn xe con ~10-20%.
   - Ngẫu nhiên: +-5% residual noise.

**Phase 2 (Real — Nếu có điều kiện mở rộng sau bảo vệ):**
Thu thập dữ liệu thực tế từ GPS và feedback: `(route_id, vehicle_type, departure_time, arrival_time)`. Cập nhật model hàng tháng.

#### Inference Flow

```
Flutter App ──> POST /api/v1/eta/predict
     │
     ▼
FastAPI ──> Kiểm tra Redis cache (fingerprint của route)
     │
     ├── Cache HIT → return cached ETA
     │
     └── Cache MISS → Feature Engineering → XGBoost predict
          │
          ▼
     Return: {
       "eta_minutes": 42.3,
       "confidence_interval": [38, 47],
       "breakdown": {
         "base_time": 32.0,
         "traffic_delay": 7.5,
         "weather_delay": 2.8,
         "vehicle_penalty": 0.0
       },
       "contributing_factors": ["rush_hour", "light_rain"]
     }
          │
          ▼
     Redis cache 5 phút
```

### 3.2. VRP Optimization — Kiến trúc chi tiết

#### Bài toán: Tối ưu GHÉP HÀNG cho tài xế đang hoàn thành cuốc xe (kịch bản "giảm chạy rỗng")

**Scenario:**
- Tài xế A đang giao hàng cuối cùng tại Quận 7, điểm đến cuối là đường Nguyễn Hữu Thọ.
- Sau khi giao xong, thay vì chạy rỗng về garage ở Quận 8, hệ thống kiểm tra các đơn hàng đang chờ:
  - Đơn B: Quận 7 → Quận 8 (2km, 50kg hàng hóa).
  - Đơn C: Quận 7 → Nhà Bè (15km, 200kg).
  - Đơn D: Quận 7 → Thủ Đức (20km, 500kg, yêu cầu 10h-12h).
- Tài xế A có sức chở xe 1.5 tấn, còn trống 1.2 tấn.
- OR-Tools tìm ra phương án tốt nhất: lấy đơn B + C trên đường về garage (chỉ chệch hướng 3km, tận dụng tải 250kg).

#### OR-Tools VRP Formulation

```python
# Mô hình toán học đơn giản hóa:
# minimize Σ(cost_km * distance(i, j) * x_{i,j,k})
# subject to:
#   Mỗi đơn hàng được gán cho 1 tài xế hoặc từ chối
#   Σ(items_weight[i]) ≤ vehicle_capacity[k]
#   Thời gian đến điểm i ∈ [time_window_start[i], time_window_end[i]]
#   Quãng đường tối đa ≤ max_route_distance[k]
#   Tài xế kết thúc tại depot hoặc điểm về nhà

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# Create routing model
manager = pywrapcp.RoutingIndexManager(
    num_locations=len(data["locations"]),
    num_vehicles=len(data["drivers"]),
    depot=0
)
routing = pywrapcp.RoutingModel(manager)

# Distance callback (từ OSRM + cache)
def distance_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return distance_matrix[from_node][to_node]  # mét

transit_callback = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback)

# Dimension: total distance per route
routing.AddDimension(
    transit_callback,
    0,  # slack
    max_route_distance,  # max distance per vehicle (mét)
    True,  # start cumul to zero
    "Distance"
)
distance_dimension = routing.GetDimensionOrDie("Distance")
distance_dimension.SetGlobalSpanCostCoefficient(100)  # cân bằng khoảng cách giữa các xe

# Dimension: time windows
# ... (tương tự)

# Constraints: vehicle capacity
demand_callback = ...  # total weight per order
routing.AddDimensionWithVehicleCapacity(
    demand_callback,
    0,  # null capacity slack
    [v.max_weight_kg for v in data["drivers"]],  # vehicle max capacities
    True,
    "Capacity"
)

# Search parameters
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)
search_parameters.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
)
search_parameters.time_limit.seconds = 30  # max solve time

solution = routing.SolveWithParameters(search_parameters)
```

#### VRP Execution Flow

```
Trigger: Tài xế hoàn thành đơn hàng (status = 'delivered')
     │
     ▼
FastAPI ──> Celery Task: optimize_route_async(driver_id)
     │
     ▼
Celery Worker ──> Lấy danh sách đơn hàng chờ trong bán kính 15km
     │              của vị trí hiện tại của tài xế
     │
     ▼
OSRM Distance Matrix ──> Tính ma trận khoảng cách 50x50
     │                     (50 đơn hàng chờ × 50 điểm)
     │
     ▼
OR-Tools Solver ──> Giải VRP với ràng buộc:
     │              - Time windows của đơn hàng
     │              - Capacity còn lại của xe
     │              - Max detour distance (chệch tối đa 10km)
     │              - Giờ nghỉ tài xế nếu gần tới
     │
     ▼
Kết quả ──> Nếu tìm thấy route tối ưu:
     │          - Push notification tới tài xế:
     │            "Có 2 đơn hàng dọc đường về: +250.000 VND,
     │             chệch chỉ 3km. Nhận?"
     │          - Chờ tài xế xác nhận
     │
     ▼
Tài xế nhận → Route được thêm vào trip hiện tại
Tài xế từ chối → Lưu kết quả cho lần optimize sau
```

#### ETA — VRP Integration

- OR-Tools gọi OSRM Distance Matrix API để lấy chi phí di chuyển giữa các cặp điểm.
- Thay vì dùng khoảng cách địa lý đơn thuần, chúng ta thay thế ma trận chi phí bằng **ETA từ XGBoost**:
  - `cost_matrix[i][j] = xgboost_predict(origin=i, dest=j, hour=current_hour, day=current_day, vehicle_type=...)`.
  - Điều này giúp OR-Tools chọn route thông minh: chọn đường đi nhanh (dù dài hơn) thay vì đường ngắn mà kẹt xe.

---

## 4. HỆ QUẢ (Consequences)

### ✅ Tích cực (Positive)
1. **ETA chính xác vượt trội so với baseline:** Dự kiến MAE < 5 phút với mock data, so với naïve baseline MAE ~15-20 phút. Đây là số liệu rất ấn tượng khi trình bày trước hội đồng.
2. **VRP giảm chi phí chạy rỗng:** Tăng utilization rate của tài xế từ 50% lên 75%+ trong mô phỏng (giảm 50% km chạy rỗng).
3. **XGBoost interpretability:** Dùng SHAP values để giải thích cho hội đồng: "Tại sao ETA là 45 phút? Vì 20% là do mưa, 30% do giờ cao điểm". Đây là điểm cộng cực lớn trong đồ án.
4. **OR-Tools explainability:** Có thể visualize solution bằng Google OR-Tools' Assignment Viewer hoặc tự vẽ trên Flutter Map.
5. **AI Agent sinh code ML hoàn hảo:** XGBoost và OR-Tools có syntax Python rất rõ ràng, AI Agent sinh được >90% code chính xác ngay từ lần đầu.
6. **Mock data pipeline:** Script sinh dữ liệu tổng hợp (synthetic data) có thể tạo hàng ngàn mẫu train trong vài phút, chứng minh được quy trình ML end-to-end.

### ⚠️ Trung tính (Neutral)
1. **Model có thể underperform trên dữ liệu thật so với mock** vì mock data không capture hết được nhiễu thực tế. Cần disclaimer trong báo cáo rằng đây là proof-of-concept với synthetic data.
2. **OR-Tools solve time tăng theo exponential với số lượng đơn hàng.** 30 đơn + 10 tài xế mất ~5 giây, 200 đơn + 50 tài xế mất ~30 giây, nhưng nếu 1000 đơn + 200 tài xế có thể không solve kịp. Trong demo, cần set giới hạn đầu vào (max 50 điểm).
3. **Cần dữ liệu thời tiết từ OpenWeather API** (free tier: 60 calls/phút, 1M calls/tháng) — đủ dùng cho demo.

### ❌ Tiêu cực (Negative)

| Rủi ro | Impact | Mitigation |
|---|---|---|
| **Thiếu dữ liệu train thực tế** cho XGBoost | Cao | Sinh mock data dựa trên OSRM travel_time với noise Gaussian theo scenario (mưa, rush hour, holiday). Model vẫn chứng minh được architecture đúng |
| **OR-Tools không tìm ra solution khả thi** do quá nhiều ràng buộc chồng chéo | Trung bình | Soft constraints: Nếu không khả thi → relax time window constraints dần dần (slack = 30 phút). Fallback: Hiển thị thông báo "Hiện tại chưa có đơn phù hợp" |
| **XGBoost overfit trên mock data** | Trung bình | Cross-validation (k=5) + early stopping + regularization parameters (reg_alpha, reg_lambda). Train/Val/Test split: 70/15/15 |

---

## 5. ĐIỀU KIỆN KIỂM TRA (Validation Criteria)

### ETA Prediction Validation

| # | Tiêu chí | Phương pháp kiểm tra | Ngưỡng chấp nhận |
|---|---|---|---|
| 1 | MAE trên test set | Load test data 20K samples, tính MAE | MAE < 5 phút |
| 2 | MAPE (Mean Absolute Percentage Error) | Tính % lỗi trên mỗi prediction | MAPE < 15% |
| 3 | R² Score | So sánh variance giải thích được | R² > 0.85 |
| 4 | So sánh với Naïve Baseline | Linear regression chỉ dùng distance | XGBoost beat baseline >30% |
| 5 | Inference latency | 1000 sequential predictions | p99 < 5ms |
| 6 | Feature importance diversity | SHAP analysis | Top 5 features không quá 60% total importance |

### VRP Optimization Validation

| # | Tiêu chí | Phương pháp kiểm tra | Ngưỡng chấp nhận |
|---|---|---|---|
| 1 | Solve time cho 50 điểm | Test 10 lần random dataset | < 30s solve time |
| 2 | Giảm km chạy rỗng | So sánh với no-optimization baseline | Giảm ≥ 40% km rỗng |
| 3 | Constraint validity | 20 test scenarios với capacity, time window, distance limit violation kiểm tra | 0 solution violation |
| 4 | Scalability | Test với 10, 20, 50, 100, 200 locations | Solve time tăng sub-linear (O(n²) thay vì O(n!)) |
| 5 | Route visualization | Vẽ solution trên Flutter Map | Tuyến đường khả thi, không tự cắt nhau, tuần tự các điểm hợp lý |

---

## 6. THAM KHẢO (References)

- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Google OR-Tools VRP Guide](https://developers.google.com/optimization/routing/vrp)
- [SHAP Values Explanation](https://shap.readthedocs.io/)
- [OR-Tools VRP Python Examples](https://github.com/google/or-tools/tree/stable/examples/python)
- [OpenWeather API for Traffic/Weather](https://openweathermap.org/api)
- ADR-003 (GIS & Routing) — Chi tiết OSRM Distance Matrix tích hợp với VRP
- ADR-004 (Database Architecture) — Lưu ETA predictions và route optimization history

---

## 7. LỊCH SỬ THAY ĐỔI (Changelog)

| Phiên bản | Ngày | Tác giả | Mô tả |
|---|---|---|---|
| 1.0 | 2026-06-15 | Tech Lead | Bản đầu tiên, quyết định XGBoost ETA + OR-Tools VRP |
