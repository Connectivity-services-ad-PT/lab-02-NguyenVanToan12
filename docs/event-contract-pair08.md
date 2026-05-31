# Event Contract sơ bộ — Cặp 08 (Core Business → Analytics)

> File này ghi nhận thỏa thuận ban đầu cho mối quan hệ Queue async giữa Core Business (Producer) và Analytics (Consumer). Chi tiết AsyncAPI / topic schema đầy đủ sẽ được phát triển trong Lab 03.

## 1. Thông tin dependency

- **Dependency số:** 8
- **Producer:** Core Business (A6/B6)
- **Consumer:** Analytics (A5/B5)
- **Cơ chế:** Queue async (Message Broker)
- **Event/topic dự kiến:**
  - `policy.decision.created`
  - `alert.created`
  - `alert.resolved`
- **Người ghi:** Nguyễn Văn Toàn (Analytics) & Đối tác đàm phán (Core Business)
- **Ngày:** 2026-05-29

---

## 2. Mục đích nghiệp vụ

- **`policy.decision.created`:** Sinh ra mỗi khi động cơ nghiệp vụ lõi (Core Business Engine) ra quyết định dựa trên chính sách bảo mật (ví dụ: cho phép/từ chối ra vào, kích hoạt phong tỏa khẩn cấp). Analytics thu thập các quyết định này để tính tỷ lệ chấp thuận/từ chối, phân tích hành vi và tối ưu hóa chính sách vận hành Smart Campus.
- **`alert.created`:** Sinh ra khi có cảnh báo bảo mật nguy hiểm được tạo từ hệ thống lõi (ví dụ: phát hiện cháy, xâm nhập trái phép). Analytics tiêu thụ để đếm số lượng sự cố, phân nhóm theo loại cảnh báo và tính toán tần suất xảy ra sự cố.
- **`alert.resolved`:** Sinh ra khi cảnh báo đã được nhân viên an ninh hoặc hệ thống xử lý xong (trạng thái RESOLVED). Analytics dùng sự kiện này kết hợp với `alert.created` để đo đếm chỉ số KPI vận hành tối quan trọng: **Mean Time to Resolve (MTTR)** (Thời gian trung bình để khắc phục sự cố).

---

## 3. Event name / topic

| Mục | Sự kiện 1: Policy Decision Created | Sự kiện 2: Alert Created | Sự kiện 3: Alert Resolved |
|---|---|---|---|
| **Event name** | `policy.decision.created` | `alert.created` | `alert.resolved` |
| **Topic/queue** | `campus.policy-decisions.v1` | `campus.alerts.created.v1` | `campus.alerts.resolved.v1` |
| **Producer** | Core Business | Core Business | Core Business |
| **Consumer** | Analytics | Analytics | Analytics |

---

## 4. Payload tối thiểu

### Sự kiện 1: `policy.decision.created`
```json
{
  "eventId": "evt_0196fb3d-aad7-7d1e-9f49-5d5148d2b111",
  "eventType": "policy.decision.created",
  "occurredAt": "2026-05-29T10:45:00.000Z",
  "correlationId": "corr_0196fb3d-abd7-7d1e-9f49-5d5148d2b222",
  "source": "core-business-service",
  "data": {
    "decisionId": "dec-0196fb3d-acd7-7d1e-9f49-5d5148d2b333",
    "policyId": "pol-access-security-high",
    "subjectId": "usr-student-20221234",
    "result": "DENIED",
    "reason": "OUT_OF_OPERATING_HOURS",
    "zoneId": "zone-it-building-main"
  }
}
```

### Sự kiện 2: `alert.created`
```json
{
  "eventId": "evt_0196fb3d-bad7-7d1e-9f49-5d5148d2b444",
  "eventType": "alert.created",
  "occurredAt": "2026-05-29T10:46:12.350Z",
  "correlationId": "corr_0196fb3d-bbd7-7d1e-9f49-5d5148d2b555",
  "source": "core-business-service",
  "data": {
    "alertId": "alt-0196fb3d-bcd7-7d1e-9f49-5d5148d2b666",
    "sourceService": "camera-stream",
    "alertType": "UNAUTHORIZED_ACCESS",
    "severity": "HIGH",
    "message": "Phat hien doi tuong la dot nhap vao phong lap chat luong cao",
    "relatedEventId": "evt_0196fb3d-7ad7-7d1e-9f49-5d5148d2bcba"
  }
}
```

### Sự kiện 3: `alert.resolved`
```json
{
  "eventId": "evt_0196fb3d-cad7-7d1e-9f49-5d5148d2b777",
  "eventType": "alert.resolved",
  "occurredAt": "2026-05-29T11:15:30.000Z",
  "correlationId": "corr_0196fb3d-bbd7-7d1e-9f49-5d5148d2b555",
  "source": "core-business-service",
  "data": {
    "alertId": "alt-0196fb3d-bcd7-7d1e-9f49-5d5148d2b666",
    "resolvedBy": "security-officer-toanNV",
    "resolutionNote": "Da kiem tra hien truong, day la giang vien vao lam viec muon, canh bao nham, da reset trang thai bao dong",
    "resolutionTimeSeconds": 1758
  }
}
```

---

## 5. Ràng buộc cần thống nhất

| Vấn đề | Quyết định tạm thời |
|---|---|
| **Lý do từ chối (Reason)** | Core Business cam kết gửi lý do dưới dạng **HẰNG SỐ CHUẨN (String Code enum)** như `OUT_OF_OPERATING_HOURS`, `BLACKLISTED`, `CREDENTIALS_EXPIRED` để Analytics có thể phân nhóm thống kê dễ dàng, thay vì gửi chuỗi text tự do. |
| **Độ khớp của correlationId** | Sự kiện `alert.created` và `alert.resolved` cho cùng một vụ việc cảnh báo **bắt buộc** phải mang cùng một `correlationId` để dễ dàng liên kết hiệu năng xử lý. |
| **Trường resolutionTimeSeconds** | Được Core Business tự động tính toán bằng hiệu số của `occurredAt` của `alert.resolved` và `alert.created` để đảm bảo số liệu chính xác đồng nhất trước khi ghi nhận. |

---

## 6. Issue chuyển sang Lab 03

1. Thống nhất danh sách chuẩn (enum) toàn bộ các mã `reason` của quyết định policy và `alertType` của cảnh báo.
2. Quy định cơ chế xử lý khi nhận được event `alert.resolved` trước khi nhận được `alert.created` (lỗi do out-of-order delivery trên network).
3. Thống nhất cơ chế bảo mật và xác thực message giữa Core Business và Analytics (sử dụng chữ ký số HMAC hoặc TLS Mutual Authentication).
