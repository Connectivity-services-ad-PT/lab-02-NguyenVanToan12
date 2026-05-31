# Biên bản đàm phán hợp đồng API & Event Contract (Phiên bản v1.0)

- **Cặp đàm phán:** Cặp 06, 07, 08, 09 (Liên quan đến phân hệ Analytics làm Consumer)
- **Product:** A (Smart Campus Operations Platform)
- **Provider (Producers):** IoT Ingestion (A1), Camera Stream (A2), Core Business (A6), Access Gate (A3)
- **Consumer:** Analytics & Alert Service (A5/B5)
- **Phiên:** v1.0 (Ký kết chính thức)
- **Ngày:** 2026-05-29

---

## Issue #1: IoT Telemetry Payload Format (Batching vs Single Event)

- **Raised by:** Consumer (Analytics)
- **Endpoint / Topic:** `campus.telemetry.v1`
- **Concern:** Ban đầu, phía IoT Ingestion đề xuất gửi gộp (batch) danh sách 100 sự kiện đo đạc trong cùng một message để giảm chi phí truyền tin. Tuy nhiên, Analytics lo ngại việc này sẽ làm tăng đột biến độ trễ (latency) khi xử lý thời gian thực và gây khó khăn khi một phần dữ liệu trong batch bị lỗi.
- **Proposal:** IoT Ingestion gửi mỗi sự kiện dưới dạng tin nhắn đơn lập (single event) kèm theo đầy đủ metadata (`eventId`, `correlationId`).
- **Resolution:** Accepted.
- **Rationale:** Việc phân tách thông điệp giúp đơn giản hóa cơ chế lọc trùng lặp và chuyển các bản tin lỗi vào Dead Letter Queue (DLQ) độc lập mà không ảnh hưởng đến các thông điệp khác.
- **Impact:** IoT Ingestion sẽ cấu hình stream publisher để phát từng tin nhắn đơn lẻ. Dung lượng trung bình mỗi message giảm xuống dưới 1KB.

---

## Issue #2: Camera Motion Event confidence score & Image References

- **Raised by:** Consumer (Analytics)
- **Endpoint / Topic:** `campus.camera-motion.v1`
- **Concern:** Camera Stream đề xuất đính kèm ảnh chụp binary của camera trực tiếp vào payload sự kiện dưới dạng Base64. Analytics phản đối mạnh mẽ vì việc nhúng ảnh binary vào Broker sẽ làm quá tải RAM và băng thông của hàng đợi Message Broker.
- **Proposal:** Camera Stream sẽ lưu ảnh chụp vào bộ lưu trữ đối tượng (Object Storage S3/MinIO) trước, sau đó chỉ đính kèm URL tham chiếu `snapshotUrl` vào payload sự kiện.
- **Resolution:** Accepted.
- **Rationale:** Giảm kích thước payload của sự kiện từ hàng Megabytes xuống còn vài trăm bytes, tối ưu hóa tốc độ phân phối tin nhắn và tải trọng của Broker.
- **Impact:** Camera Stream tích hợp module lưu trữ hình ảnh trước khi publish event. Analytics sẽ truy cập tải ảnh khi cần thông qua pre-signed URL bảo mật.

---

## Issue #3: Access Gate Direction Naming Conventions

- **Raised by:** Consumer (Analytics)
- **Endpoint / Topic:** `campus.access-logs.v1`
- **Concern:** Phía Access Gate đề xuất dùng trường `direction` mang giá trị `IN` hoặc `OUT` để chỉ hướng di chuyển. Tuy nhiên, trong sơ đồ thiết kế nghiệp vụ của Analytics và Core, hướng di chuyển được quy định rõ là `ENTER` và `EXIT`. Sự không đồng nhất này có thể gây sai lệch khi thống kê mật độ người trong khu nhà.
- **Proposal:** Thống nhất sử dụng chuẩn enum chung là `ENTER` và `EXIT` cho toàn bộ các dịch vụ.
- **Resolution:** Accepted.
- **Rationale:** Đồng bộ hóa thuật ngữ miền nghiệp vụ (Ubiquitous Language) giúp tránh các lỗi logic nghiệp vụ khi tích hợp nhiều phân hệ.
- **Impact:** Access Gate cập nhật firmware đầu đọc để mapping giá trị vật lý thành `ENTER` / `EXIT` trước khi gửi đi.

---

## Issue #4: Core Business Policy Decision Reason representation (Code vs Text)

- **Raised by:** Consumer (Analytics)
- **Endpoint / Topic:** `campus.policy-decisions.v1`
- **Concern:** Core Business gửi trường `reason` dạng chuỗi ký tự tự do (ví dụ: "The student tried to enter outside library hours"). Analytics không thể phân nhóm hay vẽ biểu đồ thống kê các lý do phổ biến dẫn tới việc từ chối truy cập nếu dữ liệu là văn bản tự do.
- **Proposal:** Chuẩn hóa trường `reason` thành dạng mã hằng số ký tự viết hoa (String Code Enum) ví dụ: `OUT_OF_OPERATING_HOURS`, `BLACKLISTED`, `INVALID_CREDENTIALS`.
- **Resolution:** Accepted.
- **Rationale:** Giúp hệ thống Analytics dễ dàng lập chỉ mục, đếm tần suất và tối ưu hóa câu lệnh truy vấn tổng hợp số liệu.
- **Impact:** Core Business định nghĩa bảng enum lý do từ chối chính thức và áp dụng kiểm tra nghiêm ngặt khi tạo quyết định.

---

## Issue #5: Correlation Id across Alert Created and Resolved

- **Raised by:** Consumer (Analytics)
- **Endpoint / Topic:** `campus.alerts.created.v1` và `campus.alerts.resolved.v1`
- **Concern:** Để đo đếm chỉ số KPI Mean Time to Resolve (MTTR), Analytics cần liên kết sự kiện cảnh báo kết thúc với sự kiện bắt đầu. Nếu không có mã liên kết chung, Analytics phải thực hiện truy vấn đắt đỏ để map thủ công.
- **Proposal:** Core Business bắt buộc phải giữ nguyên mã `correlationId` nhận được từ sự kiện `alert.created` ban đầu và truyền tiếp vào sự kiện `alert.resolved`.
- **Resolution:** Accepted.
- **Rationale:** Đảm bảo khả năng giám sát vết (End-to-End Tracing) một cách liền mạch trong kiến trúc hướng sự kiện.
- **Impact:** Core Business bổ sung trường `correlationId` làm trường bắt buộc trong luồng xử lý và lưu trữ sự cố cảnh báo.

---

## Issue #6: Anonymization of Student Card IDs

- **Raised by:** Provider (Access Gate)
- **Endpoint / Topic:** `campus.access-logs.v1`
- **Concern:** Access Gate lo ngại việc gửi trực tiếp ID thẻ sinh viên/giảng viên (`cardId` dạng số thẻ vật lý) qua hàng đợi Message Broker công khai sẽ vi phạm chính sách bảo mật thông tin cá nhân và quyền riêng tư (GDPR/Campus Privacy policy).
- **Proposal:** Access Gate thực hiện băm bảo mật (hashing) mã số thẻ bằng thuật toán SHA-256 kèm theo salt hệ thống để tạo ra trường `cardHash` trước khi truyền tin.
- **Resolution:** Accepted.
- **Rationale:** Analytics chỉ cần đếm lưu lượng và định danh duy nhất (để phát hiện trùng) mà không cần giải mã ngược số thẻ gốc của người dùng.
- **Impact:** Access Gate triển khai hàm băm SHA-256 trên thiết bị. Analytics cập nhật DB chỉ lưu trữ trường `cardHash` dài 64 ký tự.

---

# Chốt hợp đồng v1.0

- **Provider sign-off:** Nguyễn Văn Toàn (đại diện cho Analytics & Alert API)
- **Consumer sign-off:** Nguyễn Văn Toàn (đại diện cho Analytics & Alert API)
- **Witness (GV/TA):** FIT4110 Teaching Team
- **Date:** 2026-05-29

---

## Ghi chú warning nếu Spectral còn cảnh báo

| Warning | Lý do chấp nhận tạm thời | Kế hoạch sửa |
|---|---|---|
| Không có warning | Hợp đồng hoàn toàn tuân thủ chặt chẽ Spectral Ruleset | N/A |
