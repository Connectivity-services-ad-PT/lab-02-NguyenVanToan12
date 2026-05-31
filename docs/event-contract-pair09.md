# Event Contract sơ bộ — Cặp 09 (Access Gate → Analytics)

> File này ghi nhận thỏa thuận ban đầu cho mối quan hệ Queue async giữa Access Gate (Producer) và Analytics (Consumer). Chi tiết AsyncAPI / topic schema đầy đủ sẽ được phát triển trong Lab 03.

## 1. Thông tin dependency

- **Dependency số:** 9
- **Producer:** Access Gate (A3/B3)
- **Consumer:** Analytics (A5/B5)
- **Cơ chế:** Queue async (Message Broker)
- **Event/topic dự kiến:**
  - `access.log.created`
  - `access.denied`
- **Người ghi:** Nguyễn Văn Toàn (Analytics) & Đối tác đàm phán (Access Gate)
- **Ngày:** 2026-05-29

---

## 2. Mục đích nghiệp vụ

- **`access.log.created`:** Phát sinh ngay khi một lượt quẹt thẻ thành công tại cổng kiểm soát ra/vào. Analytics tiêu thụ để thống kê mật độ người, nhận diện khung giờ cao điểm tại từng cổng và tòa nhà, hỗ trợ quản lý giao thông nội khu Smart Campus.
- **`access.denied`:** Phát sinh khi có lượt quẹt thẻ không hợp lệ (thẻ giả, sai phân quyền, sai khung giờ). Analytics tiêu thụ nhằm thống kê tỷ lệ từ chối phục vụ, giúp phát hiện sớm các hành vi đột nhập hoặc lỗi phần cứng đầu đọc thẻ để bảo trì kịp thời.

---

## 3. Event name / topic

| Mục | Sự kiện 1: Access Log Created | Sự kiện 2: Access Denied |
|---|---|---|
| **Event name** | `access.log.created` | `access.denied` |
| **Topic/queue** | `campus.access-logs.v1` | `campus.access-denied.v1` |
| **Producer** | Access Gate | Access Gate |
| **Consumer** | Analytics | Analytics |

---

## 4. Payload tối thiểu

### Sự kiện 1: `access.log.created`
```json
{
  "eventId": "evt_0196fb3d-dad7-7d1e-9f49-5d5148d2b888",
  "eventType": "access.log.created",
  "occurredAt": "2026-05-29T11:00:00.000Z",
  "correlationId": "corr_0196fb3d-dcd7-7d1e-9f49-5d5148d2b999",
  "source": "access-gate-service",
  "data": {
    "logId": "log-0196fb3d-ded7-7d1e-9f49-5d5148d2baaa",
    "gateId": "gate-lib-01",
    "cardHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "direction": "ENTER",
    "accessStatus": "SUCCESS"
  }
}
```

### Sự kiện 2: `access.denied`
```json
{
  "eventId": "evt_0196fb3d-ead7-7d1e-9f49-5d5148d2bbbb",
  "eventType": "access.denied",
  "occurredAt": "2026-05-29T11:00:05.150Z",
  "correlationId": "corr_0196fb3d-ecd7-7d1e-9f49-5d5148d2bccc",
  "source": "access-gate-service",
  "data": {
    "logId": "log-0196fb3d-eed7-7d1e-9f49-5d5148d2bddd",
    "gateId": "gate-lib-01",
    "cardHash": "8f438a0a2dfca5932df27fcd72f6a9e224e75878d65cbb66835261eb8fb95471",
    "direction": "ENTER",
    "denyReason": "INVALID_PERMISSION",
    "attemptCount": 3
  }
}
```

---

## 5. Ràng buộc cần thống nhất

| Vấn đề | Quyết định tạm thời |
|---|---|
| **Hướng di chuyển (Direction)** | Thống nhất sử dụng chuẩn **`ENTER`** và **`EXIT`** (thay vì `IN`/`OUT` hay `GO`/`BACK`) để mô tả chiều di chuyển của đối tượng qua cổng. |
| **Bảo vệ thông tin cá nhân** | Tuyệt đối không gửi mã số thẻ (cardId) gốc của sinh viên/giảng viên qua queue. Access Gate bắt buộc băm bằng thuật toán SHA-256 để tạo ra trường **`cardHash`**, đảm bảo tính ẩn danh dữ liệu (Privacy-by-Design) khi Analytics lưu trữ phục vụ thống kê. |
| **Tạo log khi lỗi kết nối phần cứng** | Lượt quẹt thẻ lỗi phần cứng đầu đọc thẻ vẫn phải sinh ra `access.denied` kèm `denyReason: HARDWARE_ERROR` để Analytics theo dõi chất lượng cổng vật lý. |

---

## 6. Issue chuyển sang Lab 03

1. Định nghĩa chi tiết bảng danh mục các cổng (`gateId`) và tòa nhà tương ứng để Analytics chuẩn hóa dữ liệu báo cáo.
2. Thống nhất cách xử lý trùng lặp sự kiện khi người dùng quẹt thẻ liên tiếp nhiều lần tại đầu đọc do sốt ruột (đề xuất debounce 3 giây tại Access Gate).
3. Thiết lập chính sách bảo mật chống giả mạo thông điệp (Tampering) trên đường truyền Broker.
