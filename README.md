# YOLOv8 Object Detection Web Application

Ứng dụng web nhận diện vật thể trong hình ảnh và video ngắn sử dụng mô hình pre-trained YOLOv8 (Ultralytics), kết hợp **FastAPI** (Backend) và **React + Vite** (Frontend). Toàn bộ hệ thống được đóng gói và điều phối tự động bằng **Docker Compose**.

---

## 1. Luồng xử lý của hệ thống (Architecture)

```text
[ Trình duyệt / Client ]
   │
   ├── (1) Tải giao diện SPA: GET :5173 ──► [ Frontend Container (Nginx) ]
   │
   └── (2) Gửi ảnh/video: POST :8000/api/detect ──► [ Backend Container (FastAPI + YOLOv8) ]
```

---

## 2. Cấu trúc thư mục dự án (Project Structure)

```text
.
├── backend/
│   ├── Dockerfile              # Container hóa FastAPI (non-root appuser, pip cache)
│   ├── .dockerignore
│   ├── main.py                 # Mã nguồn API & nạp YOLOv8
│   ├── test_main.py            # Bộ ca kiểm thử tự động (pytest)
│   └── requirements.txt        # Danh sách thư viện Python
├── frontend/
│   ├── Dockerfile              # Multi-stage build (Node build -> Nginx alpine)
│   ├── .dockerignore
│   ├── src/                    # Mã nguồn React
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── compose.yaml                # Điều phối cụm container qua mạng ảo yolo-net
├── .env.example                # File biến môi trường mẫu
├── .gitignore
└── README.md
```

---

## 3. Hướng dẫn khởi chạy nhanh (Quick Start with Docker)

### Yêu cầu môi trường
* Đã cài đặt **Docker Engine** (20.10+) và **Docker Compose V2**.

### Các bước khởi chạy

1. **Khởi tạo biến môi trường:**
   ```bash
   cp .env.example .env
   ```

2. **Build và khởi chạy toàn bộ hệ thống bằng một lệnh:**
   ```bash
   docker compose up --build -d
   ```

3. **Truy cập dịch vụ:**
   * **Giao diện người dùng (Frontend):** http://localhost:5173
   * **Tài liệu tương tác API (Swagger UI):** http://localhost:8000/docs
   * **Kiểm tra trạng thái (Healthcheck):** http://localhost:8000/health

4. **Dừng hệ thống:**
   ```bash
   docker compose down
   ```

---

## 4. Danh sách API Endpoints

| Method | Endpoint | Tham số gửi lên (Form-data) | Định dạng trả về | Chức năng |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/health` | Không có | `application/json` | Kiểm tra trạng thái máy chủ (phục vụ Docker Healthcheck) |
| **POST** | `/api/detect/image` | `file`: UploadFile<br>`confidence`: float (`0.25`) | `image/jpeg` | Nhận diện vật thể trên ảnh và trả về ảnh đã vẽ bounding box |
| **POST** | `/api/detect/video` | `file`: UploadFile<br>`confidence`: float (`0.25`) | `video/mp4` | Nhận diện từng frame video và xuất file MP4 kết quả |

---

## 5. Quy chuẩn kiểm tra dữ liệu & Xử lý lỗi (Validation & Errors)

* **Ràng buộc đầu vào:**
  * **Định dạng file:** Ảnh (`.jpg`, `.jpeg`, `.png`), Video (`.mp4`).
  * **Giới hạn dung lượng:** Tối đa 10MB.
* **Mã lỗi phản hồi:**
  * `415 Unsupported Media Type`: File tải lên sai định dạng yêu cầu.
  * `413 Request Entity Too Large`: Dung lượng vượt quá giới hạn cho phép.
  * `400 Bad Request`: File lỗi hoặc không giải mã được bằng OpenCV.
  * `500 Internal Server Error`: Lỗi xử lý luồng nhận diện hoặc xuất file.

---

## 6. Kiểm thử tự động (Automated Tests)

Chạy bộ 3 ca kiểm thử tự động (Healthcheck, Valid detection, Invalid format rejection) trực tiếp bên trong container backend:

```bash
docker exec -it yolo-backend-app pytest test_main.py -v
```

---

## 7. Giới hạn kỹ thuật (Limitations)

1. **Lưu trữ dữ liệu:** Dữ liệu ảnh/video xử lý tạm thời trong container, chưa cấu hình volume lưu trữ vĩnh viễn.
2. **Xử lý video:** Quá trình nhận diện video xử lý đồng bộ trực tiếp trên luồng chính, chưa có hàng đợi tác vụ (Message Queue).
3. **Môi trường suy luận:** Mô hình YOLOv8 thực thi bằng CPU, chưa tích hợp tăng tốc phần cứng qua GPU/CUDA.

---
