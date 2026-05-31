# Phân tích yêu cầu — vai Provider (Analytics / Alert API)

- **Cặp đàm phán:** Cặp 06, 07, 08, 09
- **Product:** A
- **Provider service:** Analytics & Alert Service (A5/B5)
- **Consumer service:** Core Business (A6), Dashboard/Notification, và các dịch vụ thụ hưởng dữ liệu phân tích khác
- **Người viết:** Nguyễn Văn Toàn
- **Ngày:** 2026-05-29

---

## 1. Resource chính

| Resource | Mô tả | Thuộc tính bắt buộc | Thuộc tính tùy chọn |
|---|---|---|---|
| `Alert` | Thông tin cơ bản về cảnh báo sự cố | `id`, `title`, `severity` | `description` |
| `AlertDetail` | Chi tiết cảnh báo chuyên sâu phân loại theo kiểu cụ thể (`oneOf` FireAlert / SecurityAlert) | `alertType`, `id`, `location` (Fire) hoặc `cameraId` (Security) | `temperature`, `suspectDetected` |

---

## 2. Action/API dự kiến

| Method | Path | Mục đích | Consumer gọi khi nào? |
|---|---|---|---|
| GET | `/health` | Kiểm tra trạng thái hoạt động của hệ thống | Định kỳ bởi API Gateway hoặc Prometheus để giám sát sức khỏe |
| POST | `/alerts` | Tạo một cảnh báo khẩn cấp mới trên Smart Campus | Khi Core Business phát hiện sự cố khẩn cấp cần ghi nhận |
| GET | `/alerts/recent` | Lấy danh sách các cảnh báo gần đây nhất | Khi Dashboard/Notification cần hiển thị danh sách cho điều hành viên |
| GET | `/alerts/{alertId}` | Lấy thông tin chi tiết một cảnh báo | Khi người dùng click chọn xem chi tiết sự cố trên Dashboard |

---

## 3. Error case

Tối thiểu 5 case.

| Status | Tình huống | Response body dự kiến |
|---:|---|---|
| 400 | Payload tạo cảnh báo sai định dạng JSON hoặc thiếu trường bắt buộc | `ProblemDetails` (`application/problem+json`) |
| 401 | Thiếu JWT token hoặc định dạng header Authorization không hợp lệ | `ProblemDetails` (`application/problem+json`) |
| 403 | Token hợp lệ nhưng không được phân vai trò thích hợp | `ProblemDetails` (`application/problem+json`) |
| 404 | Không tìm thấy mã `alertId` yêu cầu trong cơ sở dữ liệu | `ProblemDetails` (`application/problem+json`) |
| 422 | Vi phạm ràng buộc nghiệp vụ (ví dụ: nhiệt độ quá cao nhưng không phải là FIRE) | `ProblemDetails` (`application/problem+json`) |

---

## 4. Giả định bổ sung

- **Giả định 1:** Phân hệ Gateway đã xử lý các vấn đề CORS, SSL Termination và Rate Limiting cơ bản trước khi chuyển request đến Analytics.
- **Giả định 2:** Dữ liệu Alert được lưu trữ persistent tối thiểu trong vòng 6 tháng trước khi archive.
- **Giả định 3:** Toàn bộ các API đều sử dụng giao tiếp an toàn qua HTTPS và mã hóa token JWT bằng khóa chung của Smart Campus.

---

## 5. Câu hỏi cho Consumer

1. Các bạn cần lấy danh sách cảnh báo `/alerts/recent` theo bộ lọc cụ thể nào (ví dụ: filter theo severity hay zoneId)?
2. Tần suất tải trang Dashboard/gọi API của các bạn là bao nhiêu để chúng tôi tối ưu caching (Redis)?
3. Kích thước trang mặc định (page limit) cho Cursor-based pagination mà các bạn mong muốn là bao nhiêu (đề xuất: 20)?

---

## 6. Rủi ro tích hợp

| Rủi ro | Tác động | Đề xuất xử lý |
|---|---|---|
| Số lượng cảnh báo quá lớn làm chậm API | Dashboard bị nghẽn, lag | Ép buộc sử dụng Cursor-based pagination và không cho phép lấy toàn bộ dữ liệu cùng lúc |
| Sai lệch thông tin AlertDetail do sai discriminator | Consumer không parse được dynamic schema | Thực hiện kiểm duyệt chặt chẽ (strict validation) đầu vào POST `/alerts` theo đúng schema |
