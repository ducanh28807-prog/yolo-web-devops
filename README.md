# YOLOv8 Object Detection Web Application (Week 2 & Week 3 Milestone)

Ứng dụng web nhận diện vật thể trong hình ảnh và video ngắn sử dụng mô hình pre-trained YOLOv8 (Ultralytics), kết hợp **FastAPI** (Backend) và **React + Vite** (Frontend). Hệ thống được đóng gói hoàn chỉnh bằng **Docker** và điều phối qua **Docker Compose V2** với các chuẩn tối ưu hóa: Multi-stage build, Non-root user, pip layer caching và Healthcheck gating.

---

## 1. Kiến trúc hệ thống & Luồng xử lý (Architecture & Request Flow)

Hệ thống hoạt động theo mô hình Microservices phân tách độc lập giữa dịch vụ phân phối giao diện tĩnh (Frontend Delivery) và dịch vụ xử lý logic AI (Backend API):

```text
[ Trình duyệt / Client (Máy người dùng) ]
   │
   ├── (1) Tải giao diện SPA: GET http://localhost:5173
   │        │
   │        ▼
   │   [ Docker Port Mapping: 5173 ──> 80 ]
   │        │
   │        ▼
   │   ┌─────────────────────────────────────────────────────────┐
   │   │ Container: yolo-frontend-app                            │
   │   │ Base: nginx:alpine | Phục vụ file tĩnh (/dist)          │
   │   └─────────────────────────────────────────────────────────┘
   │
   └── (2) Gửi ảnh/video nhận diện: POST http://localhost:8000/api/detect/*
            │
            ▼
       [ Docker Port Mapping: 8000 ──> 8000 ]
            │
            ▼
       ┌─────────────────────────────────────────────────────────┐
       │ Container: yolo-backend-app                             │
       │ Base: python:3.10-slim | Non-root User (appuser:1000)   │
       │ Uvicorn Server lắng nghe 0.0.0.0:8000                   │
       │ Nạp mô hình YOLOv8n, xử lý bounding box và trả kết quả  │
       └─────────────────────────────────────────────────────────┘
            ▲                                           ▲
            └──────────────[ yolo-net ]─────────────────┘
                     (Mạng ảo Docker Bridge nội bộ)
