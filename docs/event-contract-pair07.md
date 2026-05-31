# Event Contract sơ bộ — Cặp 07 (Camera Stream → Analytics)

> File này ghi nhận thỏa thuận ban đầu cho mối quan hệ Queue async giữa Camera Stream (Producer) và Analytics (Consumer). Chi tiết AsyncAPI / topic schema đầy đủ sẽ được phát triển trong Lab 03.

## 1. Thông tin dependency

- **Dependency số:** 7
- **Producer:** Camera Stream (A2/B2)
- **Consumer:** Analytics (A5/B5)
- **Cơ chế:** Queue async (Message Broker)
- **Event/topic dự kiến:**
  - `camera.motion.detected`
  - `camera.frame.analyzed`
  - `camera.status.changed`
- **Người ghi:** Nguyễn Văn Toàn (Analytics) & Đối tác đàm phán (Camera Stream)
- **Ngày:** 2026-05-29

---

## 2. Mục đích nghiệp vụ

- **`camera.motion.detected`:** Phát ra khi camera ghi nhận chuyển động trong vùng quan sát. Analytics dùng sự kiện này để đếm tần suất chuyển động tại các khu vực nhạy cảm theo thời gian thực (ví dụ: bãi đỗ xe ngoài giờ, hành lang ban đêm).
- **`camera.frame.analyzed`:** Sinh ra sau khi một frame hình ảnh từ camera được AI phân tích thành công (chứa detectionId, số lượng người, vật thể được phát hiện). Analytics sử dụng để vẽ bản đồ nhiệt mật độ (Heatmap) và thống kê lưu lượng người tại Smart Campus.
- **`camera.status.changed`:** Phát ra khi camera bị mất kết nối (Offline) hoặc kết nối lại (Online). Analytics dùng sự kiện này để theo dõi sức khỏe thiết bị phần cứng, hiển thị cảnh báo lên trung tâm điều hành campus.

---

## 3. Event name / topic

| Mục | Sự kiện 1: Motion Detected | Sự kiện 2: Frame Analyzed | Sự kiện 3: Status Changed |
|---|---|---|---|
| **Event name** | `camera.motion.detected` | `camera.frame.analyzed` | `camera.status.changed` |
| **Topic/queue** | `campus.camera-motion.v1` | `campus.camera-analysis.v1` | `campus.camera-status.v1` |
| **Producer** | Camera Stream | Camera Stream | Camera Stream |
| **Consumer** | Analytics | Analytics | Analytics |

---

## 4. Payload tối thiểu

### Sự kiện 1: `camera.motion.detected`
```json
{
  "eventId": "evt_0196fb3d-7ad7-7d1e-9f49-5d5148d2bcba",
  "eventType": "camera.motion.detected",
  "occurredAt": "2026-05-29T10:35:00.500Z",
  "correlationId": "corr_0196fb3d-7bd7-7d1e-9f49-5d5148d2bccc",
  "source": "camera-stream-service",
  "data": {
    "cameraId": "cam-gate-01",
    "location": "MAIN_GATE",
    "motionAreaRatio": 0.35,
    "confidence": 0.92,
    "snapshotUrl": "https://storage.smartcampus.edu.vn/snapshots/2026/05/29/cam-gate-01_103500.jpg"
  }
}
```

### Sự kiện 2: `camera.frame.analyzed`
```json
{
  "eventId": "evt_0196fb3d-8ad7-7d1e-9f49-5d5148d2bddd",
  "eventType": "camera.frame.analyzed",
  "occurredAt": "2026-05-29T10:35:01.000Z",
  "correlationId": "corr_0196fb3d-7bd7-7d1e-9f49-5d5148d2bccc",
  "source": "camera-stream-service",
  "data": {
    "detectionId": "det-0196fb3d-8bd7-7d1e-9f49-5d5148d2beee",
    "cameraId": "cam-gate-01",
    "peopleCount": 4,
    "vehiclesCount": 1,
    "detections": [
      { "label": "person", "confidence": 0.98, "box": [100, 200, 150, 300] },
      { "label": "car", "confidence": 0.95, "box": [400, 500, 480, 600] }
    ]
  }
}
```

### Sự kiện 3: `camera.status.changed`
```json
{
  "eventId": "evt_0196fb3d-9ad7-7d1e-9f49-5d5148d2bfff",
  "eventType": "camera.status.changed",
  "occurredAt": "2026-05-29T10:40:00.000Z",
  "correlationId": "corr_0196fb3d-9bd7-7d1e-9f49-5d5148d2baaa",
  "source": "camera-stream-service",
  "data": {
    "cameraId": "cam-gate-01",
    "status": "OFFLINE",
    "downtimeDurationSeconds": 0,
    "errorMsg": "STREAM_CONNECTION_REFUSED"
  }
}
```

---

## 5. Ràng buộc cần thống nhất

| Vấn đề | Quyết định tạm thời |
|---|---|
| **Event id có bắt buộc không?** | **Có.** UUIDv7 để bảo đảm thứ tự thời gian tự nhiên và tránh xử lý lặp sự kiện tại Analytics. |
| **Gửi ảnh thật hay chỉ gửi link?** | **Chỉ gửi link ảnh (imageRef/snapshotUrl).** Không bao giờ gửi trực tiếp ảnh binary vào message broker để tránh quá tải dung lượng queue. Ảnh thật được lưu trữ trên S3/MinIO và Consumer truy cập qua URL được cấp quyền. |
| **Định nghĩa camera offline** | Camera Stream sẽ sinh ra event `camera.status.changed` với status `OFFLINE` nếu không đọc được luồng video hoặc mất ping trong thời gian liên tục vượt quá **30 giây**. |

---

## 6. Issue chuyển sang Lab 03

1. Thiết kế cơ chế phân quyền (Pre-signed URL hoặc Token) để Analytics tải ảnh từ `snapshotUrl` an toàn.
2. Quy định tần suất (Rate Limit) tối đa gửi của event `camera.frame.analyzed` để tránh làm ngập (flood) hàng đợi xử lý của Analytics (đề xuất tối đa 1 frame/giây cho mỗi camera).
3. Thống nhất cách xử lý khi camera gửi event muộn (out-of-order events) do lỗi mạng.
