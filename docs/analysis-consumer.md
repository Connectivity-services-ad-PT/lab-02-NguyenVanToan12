# Phân tích yêu cầu — vai Consumer (Analytics Service)

- **Cặp đàm phán:** Cặp 06, 07, 08, 09
- **Product:** A
- **Consumer service:** Analytics Service (A5)
- **Provider services:** IoT Ingestion (A1), Camera Stream (A2), Core Business (A6), Access Gate (A3)
- **Người viết:** Nguyễn Văn Toàn
- **Ngày:** 2026-05-29

---

## 1. Resource Consumer cần nhận/gửi

| Resource | Consumer dùng để làm gì? | Field bắt buộc với Consumer | Field có thể tùy chọn |
|---|---|---|---|
| `iot.telemetry.ingested` | Thống kê và aggregate các chỉ số môi trường theo giờ/ngày | `eventId`, `eventType`, `occurredAt`, `data.deviceId`, `data.zoneId`, `data.metrics.temperature` | `data.metrics.humidity`, `correlationId` |
| `camera.frame.analyzed` | Đếm lưu lượng người, vẽ biểu đồ nhiệt mật độ Smart Campus | `eventId`, `eventType`, `occurredAt`, `data.cameraId`, `data.peopleCount` | `data.vehiclesCount`, `data.detections` |
| `policy.decision.created` | Tính toán tỷ lệ chấp thuận/từ chối của hệ thống kiểm soát | `eventId`, `eventType`, `occurredAt`, `data.decisionId`, `data.result`, `data.reason` | `data.policyId`, `data.subjectId` |
| `access.log.created` | Thống kê lưu lượng ra vào, phát hiện khung giờ cao điểm | `eventId`, `eventType`, `occurredAt`, `data.logId`, `data.gateId`, `data.direction` | `data.cardHash`, `data.accessStatus` |

---

## 2. API Consumer cần gọi (nếu có để bổ trợ)

| Method | Path | Lúc nào gọi? | Kỳ vọng response |
|---|---|---|---|
| GET | `/alerts/recent` | Lấy danh sách cảnh báo gần đây nhất để đối chiếu dữ liệu phân tích | `200 OK` + danh sách Alerts (hỗ trợ cursor pagination) |
| GET | `/alerts/{alertId}` | Lấy thông tin chi tiết một cảnh báo cụ thể để phân tích chuyên sâu | `200 OK` + chi tiết cảnh báo (`oneOf` FireAlert/SecurityAlert) |

---

## 3. Error case Consumer cần xử lý

Tối thiểu 5 case.

| Status | Consumer hiểu là gì? | Consumer sẽ xử lý thế nào? |
|---:|---|---|
| 400 | Request gửi đi sai định dạng schema | Sửa payload, ghi log lỗi nghiêm trọng và cảnh báo hệ thống giám sát |
| 401 | Thiếu hoặc hết hạn Bearer token xác thực | Tiến hành lấy token mới và retry request |
| 403 | Token hợp lệ nhưng không đủ quyền truy cập | Báo lỗi phân quyền và ghi log bảo mật |
| 404 | Resource (Alert) không tồn tại | Thông báo cho người dùng không tìm thấy tài liệu và cập nhật giao diện |
| 422 | Vi phạm quy tắc nghiệp vụ hệ thống | Hiển thị thông báo chi tiết lỗi nghiệp vụ nhận về từ Problem Details |

---

## 4. Giả định bổ sung

- **Giả định 1:** Toàn bộ thông tin định danh sự kiện bắt buộc dùng định dạng UUIDv7 để bảo đảm tính tuần tự và độc bản.
- **Giả định 2:** Định dạng thời gian `occurredAt` luôn tuân thủ chuẩn ISO-8601 kèm múi giờ UTC (`YYYY-MM-DDTHH:mm:ss.sssZ`).
- **Giả định 3:** Các Producer đảm bảo phân phối thông điệp với cam kết tối thiểu At-Least-Once, và Analytics tự cài đặt cơ chế kiểm tra trùng lặp (deduplication) tại Consumer.

---

## 5. Câu hỏi cho Provider (Producers)

1. Tốc độ sinh sự kiện tối đa (Peak RPS) của mỗi Producer là bao nhiêu để chúng tôi thiết kế buffer phù hợp?
2. Có thể đảm bảo các sự kiện liên quan cùng chung một `correlationId` để dễ truy vết xuyên suốt không?
3. Các mã lỗi hoặc mã lý do (reason codes) đã được chuẩn hóa thành dạng hằng số chưa hay là text tự do?

---

## 6. Rủi ro tích hợp

| Rủi ro | Tác động | Đề xuất xử lý |
|---|---|---|
| Provider đổi kiểu dữ liệu đột ngột | Consumer bị crash hoặc parse lỗi | Chốt chặt chẽ hợp đồng API/Event Contract, cấm phá vỡ tương thích ngược |
| Nhận sự kiện out-of-order | Sai lệch dữ liệu thống kê (ví dụ: resolved trước created) | Áp dụng cơ chế so sánh timestamp `occurredAt` và dùng hàng đợi đệm (buffer queue) |
| Trùng lặp sự kiện (Duplicate events) | Số liệu thống kê bị nhân đôi | Sử dụng `eventId` làm khóa duy nhất để thực hiện lọc trùng qua Redis |
