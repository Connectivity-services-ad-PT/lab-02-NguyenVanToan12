# Chính sách Quản lý Phiên bản API (API Versioning Policy)

Tài liệu này quy định cách thức quản lý phiên bản, chính sách vòng đời và cơ chế truyền thông tin phiên bản giữa các dịch vụ trong dự án **Smart Campus Operations Platform**.

---

## 1. Nguyên tắc cốt lõi: Semantic Versioning (SemVer 2.0.0)

Mọi API REST và Event Contract được gán nhãn phiên bản theo định dạng: `MAJOR.MINOR.PATCH`

- **MAJOR (Phá vỡ tương thích - Breaking Changes):** Tăng khi có những thay đổi không tương thích ngược với API cũ. Yêu cầu Consumer phải cập nhật mã nguồn để có thể tích hợp.
  - *Ví dụ:* Xóa một trường bắt buộc trong Response, thay đổi kiểu dữ liệu của một trường từ `string` sang `integer`, hoặc đổi tên endpoint.
- **MINOR (Tương thích ngược - Backward-Compatible Additions):** Tăng khi bổ sung chức năng mới nhưng vẫn đảm bảo tương thích ngược với các Consumer cũ.
  - *Ví dụ:* Thêm một trường tùy chọn (optional) trong request body, hoặc thêm một endpoint mới.
- **PATCH (Vá lỗi - Backward-Compatible Bug Fixes):** Tăng khi sửa lỗi nội bộ mà không làm thay đổi cấu trúc dữ liệu đầu ra/đầu vào của API.
  - *Ví dụ:* Sửa lỗi logic nghiệp vụ bên trong, tối ưu hóa tốc độ xử lý hoặc cập nhật nội dung mô tả API.

---

## 2. Định nghĩa Thay đổi Tương thích và Bất tương thích

### 2.1. Thay đổi Tương thích Ngược (Backward-Compatible Changes)
Consumer cam kết áp dụng nguyên lý **Tolerant Reader** (chỉ đọc các trường cần thiết, bỏ qua các trường lạ) để đảm bảo không bị lỗi khi Provider thực hiện các thay đổi sau:
- Bổ sung một endpoint mới hoặc phương thức HTTP mới.
- Bổ sung một trường tùy chọn (`optional`) trong Request Payload.
- Bổ sung một trường bất kỳ trong Response Payload.
- Thay đổi thứ tự xuất hiện của các trường trong đối tượng JSON.

### 2.2. Thay đổi Gây Lỗi (Breaking Changes)
Các thay đổi sau buộc phải nâng cấp phiên bản **MAJOR**:
- Xóa bỏ hoặc đổi tên một endpoint hiện hữu.
- Xóa bỏ hoặc đổi tên một trường trong Request hoặc Response.
- Thay đổi một trường từ tùy chọn (`optional`) thành bắt buộc (`required`).
- Thay đổi kiểu dữ liệu (data type) hoặc định dạng (format) của một trường hiện có.
- Thay đổi các hằng số enum trong hệ thống (ví dụ: đổi `LOW` thành `MINOR`).
- Thay đổi mã trạng thái HTTP trả về khi lỗi (ví dụ: đổi lỗi nghiệp vụ từ `400` thành `422`).

---

## 3. Quy trình Khai tử API cũ (Deprecation and Sunset)

Khi một phiên bản API chuẩn bị bị thay thế bởi phiên bản MAJOR mới, Provider cam kết thực hiện quy trình khai tử an toàn qua 3 bước:

### Bước 1: Khai báo Deprecated trong OpenAPI
- Đánh dấu trường `deprecated: true` trực tiếp trên các path hoặc operation trong tài liệu `openapi.yaml`.
- Bổ sung cảnh báo trong `description`.

### Bước 2: Gửi Header thông báo thời gian sống (Sunset & Deprecation Headers)
Khi Consumer gọi vào API cũ, Provider sẽ tự động trả về các Header tiêu chuẩn trong Response:
- **`Deprecation`:** Chỉ định ngày API chính thức bị coi là cũ kỹ hoặc chứa đường dẫn thông tin.
  - *Ví dụ:* `Deprecation: @1779840000` (dạng timestamp) hoặc `Deprecation: true`.
- **`Sunset`:** Xác định ngày giờ cụ thể mà API cũ sẽ chính thức bị tắt (shut down) hoàn toàn.
  - *Ví dụ:* `Sunset: Sun, 31 May 2026 23:59:59 GMT`

### Bước 3: Tắt dịch vụ (Hard Sunset)
Sau khi thời hạn ghi trong Header `Sunset` kết thúc (tối thiểu là 3 tháng kể từ ngày phát hành thông báo), Provider sẽ tắt hoàn toàn endpoint cũ và trả về mã lỗi `410 Gone`.

---

## 4. Cách thức truyền tải phiên bản (URI Versioning)

Dự án sử dụng phương pháp **Version in Path (URI Versioning)** cho các phiên bản lớn (MAJOR) để tăng tính rõ ràng và hỗ trợ caching tốt ở tầng Gateway:
- Địa chỉ gọi API: `https://api.smartcampus.edu.vn/v1/alerts/recent`
- Khi nâng cấp phiên bản lớn: `https://api.smartcampus.edu.vn/v2/alerts/recent`

Đối với các phiên bản MINOR và PATCH, hệ thống sẽ thực hiện cập nhật nóng (rolling update) phía backend mà không làm thay đổi đường dẫn URL.
