# Event Contract sơ bộ — Cặp 06 (IoT Ingestion → Analytics)

> File này ghi nhận thỏa thuận ban đầu cho mối quan hệ Queue async giữa IoT Ingestion (Producer) và Analytics (Consumer). Chi tiết AsyncAPI / topic schema đầy đủ sẽ được phát triển trong Lab 03.

## 1. Thông tin dependency

- **Dependency số:** 6
- **Producer:** IoT Ingestion (A1/B1)
- **Consumer:** Analytics (A5/B5)
- **Cơ chế:** Queue async (Message Broker)
- **Event/topic dự kiến:**
  - `iot.telemetry.ingested`
  - `iot.device.status.changed`
- **Người ghi:** Nguyễn Văn Toàn (Analytics) & Đối tác đàm phán (IoT Ingestion)
- **Ngày:** 2026-05-29

---

## 2. Mục đích nghiệp vụ

- **`iot.telemetry.ingested`:** Tự động sinh ra khi IoT Ingestion nhận được dữ liệu đo đạc (nhiệt độ, độ ẩm, trạng thái) từ các thiết bị cảm biến trên Smart Campus. Analytics tiêu thụ sự kiện này để tính toán các số liệu thống kê (trung bình, giá trị lớn nhất/nhỏ nhất) theo giờ/ngày phục vụ hiển thị biểu đồ trên dashboard.
- **`iot.device.status.changed`:** Sinh ra khi một thiết bị thay đổi trạng thái hoạt động (Online, Offline, Maintenance, Error). Analytics dùng để theo dõi hiệu suất hoạt động và tính toán tỷ lệ khả dụng (Uptime/Availability SLA) của thiết bị campus.

---

## 3. Event name / topic

| Mục | Sự kiện 1: Telemetry Ingested | Sự kiện 2: Device Status Changed |
|---|---|---|
| **Event name** | `iot.telemetry.ingested` | `iot.device.status.changed` |
| **Topic/queue** | `campus.telemetry.v1` | `campus.device-status.v1` |
| **Producer** | IoT Ingestion | IoT Ingestion |
| **Consumer** | Analytics | Analytics |

---

## 4. Payload tối thiểu

### Sự kiện 1: `iot.telemetry.ingested`
```json
{
  "eventId": "evt_0196fb3d-4ad7-7d1e-9f49-5d5148d2babc",
  "eventType": "iot.telemetry.ingested",
  "occurredAt": "2026-05-29T10:30:00.123Z",
  "correlationId": "corr_0196fb3d-4bd7-7d1e-9f49-5d5148d2bcde",
  "source": "iot-ingestion-service",
  "data": {
    "deviceId": "dev-temp-0042",
    "deviceType": "TEMPERATURE_SENSOR",
    "zoneId": "zone-library-fl2",
    "metrics": {
      "temperature": 24.5,
      "humidity": 55.0
    }
  }
}
```

### Sự kiện 2: `iot.device.status.changed`
```json
{
  "eventId": "evt_0196fb3d-5ad7-7d1e-9f49-5d5148d2bfff",
  "eventType": "iot.device.status.changed",
  "occurredAt": "2026-05-29T10:32:15.000Z",
  "correlationId": "corr_0196fb3d-5bd7-7d1e-9f49-5d5148d2baaa",
  "source": "iot-ingestion-service",
  "data": {
    "deviceId": "dev-temp-0042",
    "previousStatus": "ONLINE",
    "newStatus": "ERROR",
    "reason": "CONNECTION_TIMEOUT",
    "pingLatencyMs": 1500
  }
}
```

---

## 5. Ràng buộc cần thống nhất

| Vấn đề | Quyết định tạm thời |
|---|---|
| **Event id có bắt buộc không?** | **Có.** Phải dùng định dạng UUIDv7 (hoặc dạng string prefix `evt_` + UUID) để phục vụ deduplication (chống xử lý lặp) tại Consumer. |
| **Có cần correlationId không?** | **Có.** Giúp trace dấu chân của luồng dữ liệu từ thiết bị vật lý qua Ingestion đến Analytics. |
| **Có cho phép gửi trùng event không?** | **Có thể.** Hệ thống truyền tin đảm bảo At-Least-Once. Analytics cam kết triển khai cơ chế **Idempotent Consumer** dựa trên `eventId` làm khóa lưu vào Redis cache trong vòng 24 giờ. |
| **Cách xử lý dữ liệu lỗi định dạng** | Dữ liệu lỗi JSON sẽ bị đẩy vào **Dead Letter Queue (DLQ)** của hệ thống Message Broker để kỹ sư kiểm tra, tránh làm tắc nghẽn queue chính. |

---

## 6. Issue chuyển sang Lab 03

1. Định nghĩa chính xác định dạng và các metric được hỗ trợ cho từng loại `deviceType` (ví dụ: cảm biến ánh sáng, cảm biến chuyển động, cảm biến điện năng).
2. Quy định cơ chế backoff retry và cấu hình thời gian sống (TTL) của thông điệp trong queue trước khi đưa vào DLQ.
3. Thống nhất cơ chế nén payload khi dung lượng của thông điệp vượt quá 256KB.
