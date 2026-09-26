# Ứng Dụng Nhận Diện Vật Thể Thời Gian Thực (YOLOv8 + FastAPI + React)

Dự án đóng gói hệ thống **Full-stack AI** phục vụ bài toán nhận diện vật thể trên hình ảnh và video sử dụng mô hình **YOLOv8**.

Toàn bộ hệ thống được container hóa bằng **Docker + Docker Compose**, triển khai theo mô hình **Reverse Proxy chuẩn production** với một điểm truy cập duy nhất thông qua Nginx.

---

# 1. Kiến Trúc Hệ Thống (System Architecture)

Hệ thống được thiết kế theo mô hình **Single Entry Point** nhằm đảm bảo:

- Không expose trực tiếp Backend ra bên ngoài.
- Toàn bộ request đi qua Nginx Reverse Proxy.
- Tách biệt frontend và backend bằng Docker Network nội bộ.

```
                    Client / Browser
                          |
                          |
                    HTTP Port 80
                          |
                          ▼
┌──────────────────────────────────────────────┐
│          CONTAINER: yolo-frontend-app        │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ Nginx Web Server                       │  │
│  │ - Serve React SPA                      │  │
│  │ - Reverse Proxy                        │  │
│  └────────────────────────────────────────┘  │
│                                              │
│       /api/*  ───────────────┐              │
│       /static/* ─────────────┼──────┐       │
└──────────────────────────────┼──────┼───────┘
                               │      │
              Docker Bridge Network (yolo-net)
                               │      │
                               ▼      ▼

┌──────────────────────────────────────────────┐
│           CONTAINER: yolo-backend-app        │
│                                              │
│  - FastAPI / Uvicorn Server                  │
│  - YOLOv8 Inference Engine                   │
│  - Video Processing (FFmpeg H.264)            │
│  - Static File Storage                       │
│                                              │
│  Internal Port: 8000                         │
└──────────────────────────────────────────────┘
```

---

## Các Điểm Nổi Bật Về Mặt Kỹ Thuật

### 1. Multi-Stage Build (Frontend)

Frontend sử dụng Docker Multi-stage Build:

- Stage 1: `Node:20-alpine`
  - Cài đặt dependencies.
  - Build React production bundle.

- Stage 2: `Nginx:alpine`
  - Serve file tĩnh.
  - Chạy Reverse Proxy.

Giúp giảm kích thước Docker image từ khoảng **1GB xuống còn ~25MB**.

---

### 2. Internal Network Isolation

Backend không sử dụng `ports` để expose ra host.

Thay vào đó:

```yaml
expose:
  - "8000"
```

Điều này giúp:

- Backend chỉ có thể truy cập trong Docker Network.
- Không mở trực tiếp API ra Internet.
- Tăng tính bảo mật hệ thống.

---

### 3. Reverse Proxy Pattern

Nginx frontend đảm nhiệm hai vai trò:

### Static Server

Phục vụ React SPA:

```
/
```

### Reverse Proxy

Chuyển tiếp request:

```
/api/*
        |
        ▼
http://backend:8000
```

và:

```
/static/*
        |
        ▼
Backend Static Storage
```

Docker DNS nội bộ tự động phân giải hostname:

```
backend → container backend
```

---

### 4. Automatic Temporary File Cleanup

Backend sử dụng:

- FastAPI `BackgroundTasks`
- FFmpeg H.264 encoding

Để:

- Xử lý video upload.
- Trả kết quả về client.
- Tự động xóa file tạm sau khi hoàn thành nếu người dùng không lưu.

---

### 5. Healthcheck Synchronization

Frontend chỉ được khởi động khi Backend đã sẵn sàng:

```yaml
condition: service_healthy
```

Giúp tránh tình trạng:

- Frontend chạy trước.
- API chưa hoạt động.
- Request thất bại khi startup.

---

# 2. Cấu Trúc Thư Mục (Directory Structure)

```
.
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   ├── yolov8n.pt
│   └── static/
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
│       └── App.jsx
│
├── compose.yaml
├── .env
└── README.md
```

---

# 3. Hướng Dẫn Cài Đặt & Vận Hành

## Yêu cầu hệ thống

- Docker Engine >= 20.10
- Docker Compose >= 2.0

---

## Khởi chạy hệ thống

Tại thư mục chứa `compose.yaml`:

```bash
docker compose up -d --build
```

Lệnh trên sẽ:

- Build frontend image.
- Build backend image.
- Tạo Docker Network.
- Khởi chạy toàn bộ container.

---

## Kiểm tra trạng thái container

```bash
docker compose ps
```

Kết quả mong đợi:

```
yolo-backend-app     healthy
yolo-frontend-app    0.0.0.0:80->80/tcp
```

---

## Truy cập ứng dụng

Mở trình duyệt:

```
http://localhost
```

Hoặc:

```
http://<IP_MAY_AO>
```

---

## Swagger API Documentation

Có thể truy cập thông qua Reverse Proxy:

```
http://localhost/docs
```

---

## Dừng hệ thống

```bash
docker compose down
```

Lệnh này sẽ:

- Stop container.
- Xóa container.
- Dọn Docker Network.

---

# 4. API Endpoints Chính

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/health` | Kiểm tra trạng thái dịch vụ |
| GET | `/api/results` | Lấy danh sách file kết quả |
| POST | `/api/detect/image` | Nhận diện vật thể trên ảnh |
| POST | `/api/detect/video` | Nhận diện vật thể trên video |
| GET | `/static/{filename}` | Truy cập file kết quả |

---

# 5. Quy Trình Cập Nhật Dự Án

Sau khi hoàn thành thay đổi:

```bash
git add .
```

Commit:

```bash
git commit -m "feat(infra): finalize reverse proxy, isolate backend network and add documentation"
```

Push:

```bash
git push origin <ten-nhanh>
```

---

# 6. Tổng Kết

Dự án triển khai đầy đủ pipeline:

```
React Frontend
        |
        ▼
Nginx Reverse Proxy
        |
        ▼
FastAPI Backend
        |
        ▼
YOLOv8 Inference Engine
        |
        ▼
Image / Video Result
```

Các thành phần chính:

- ✅ React SPA frontend
- ✅ FastAPI REST API
- ✅ YOLOv8 Object Detection
- ✅ Docker Containerization
- ✅ Docker Compose Orchestration
- ✅ Nginx Reverse Proxy
- ✅ Internal Network Isolation
- ✅ Healthcheck Synchronization
- ✅ Automated Temporary File Cleanup

Hệ thống đáp ứng mô hình triển khai Full-stack AI gần với môi trường production.
