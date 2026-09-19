# YOLOv8 Object Detection Web Application

![CI Status](https://github.com/ducanh28807-prog/yolo-web-devops/actions/workflows/ci.yml/badge.svg)
![Build & Publish](https://github.com/ducanh28807-prog/yolo-web-devops/actions/workflows/build-and-publish.yml/badge.svg)

Ứng dụng web nhận diện vật thể trong hình ảnh và video ngắn sử dụng mô hình pre-trained **YOLOv8 (Ultralytics)**, kết hợp **FastAPI** (Backend) và **React + Vite** (Frontend).

Hệ thống hỗ trợ lưu trữ kết quả bền vững qua **Docker Volume**, tự động dọn dẹp file tạm và triển khai pipeline **CI/CD hoàn chỉnh với GitHub Actions & GitHub Container Registry (GHCR)**.

---

## 1. Luồng xử lý của hệ thống (Architecture)

```text
[ Trình duyệt / Client ]
   │
   ├── (1) Tải giao diện SPA: GET :5173
   │                │
   │                ▼
   │       [ Frontend Container ]
   │              Nginx
   │
   ├── (2) Gửi ảnh/video:
   │       POST :8000/api/detect/image
   │       POST :8000/api/detect/video
   │                │
   │                ▼
   │       [ Backend Container ]
   │        FastAPI + YOLOv8
   │
   └── (3) Xem lịch sử/kết quả:
           GET :8000/api/results
                    │
                    ▼
           [ Docker Host Volume ]
             ./backend/static
```

### Các thành phần chính

- **Frontend:** React + Vite, được build thành static files và phục vụ bởi Nginx.
- **Backend:** FastAPI xử lý API request và thực hiện suy luận bằng YOLOv8.
- **Storage:** `./backend/static` được mount vào container để lưu kết quả bền vững.
- **Network:** Các container giao tiếp với nhau thông qua Docker network `yolo-net`.
- **CI/CD:** GitHub Actions tự động kiểm thử, build và publish Docker images lên GHCR.

---

## 2. Cấu trúc thư mục dự án (Project Structure)

```text
.
├── .github/
│   └── workflows/
│       ├── ci.yml
│       │   └── PR gating workflow
│       │       (Lint, Pytest, Docker Build dry-run)
│       │
│       └── build-and-publish.yml
│           └── Release workflow
│               (Publish images lên GHCR)
│
├── backend/
│   ├── Dockerfile
│   │   └── Container hóa FastAPI
│   │       (non-root appuser, libgl1)
│   │
│   ├── .dockerignore
│   ├── main.py
│   │   └── API, YOLO inference,
│   │       BackgroundTasks dọn dẹp file tạm
│   │
│   ├── test_main.py
│   │   └── Bộ ca kiểm thử tự động (pytest)
│   │
│   ├── requirements.txt
│   │   └── Danh sách thư viện Python
│   │
│   └── static/
│       └── Thư mục lưu trữ kết quả
│           (Mount volume ra host)
│
├── frontend/
│   ├── Dockerfile
│   │   └── Multi-stage build
│   │       (Node 20 build → Nginx Alpine)
│   │
│   ├── .dockerignore
│   ├── src/
│   │   └── Mã nguồn React
│   │       (Dashboard nhận diện & Gallery lịch sử)
│   │
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── compose.yaml
│   └── Điều phối cụm container
│       qua mạng ảo yolo-net
│
├── .env.example
│   └── File biến môi trường mẫu
│
├── .gitignore
└── README.md
```

---

## 3. CI/CD Pipeline & Container Registry (Week 4)

Hệ thống tự động hóa chu trình kiểm thử và đóng gói phần mềm thông qua **2 GitHub Actions workflows**.

### 3.1. Pull Request Verification (`ci.yml`)

- **Trigger:** Kích hoạt tự động khi mở hoặc cập nhật Pull Request trỏ vào nhánh `main`.

- **Backend CI:**
  - Cài đặt các dependency hệ thống như `libgl1` và `libglib2.0-0`.
  - Kiểm tra cú pháp và chuẩn mã nguồn bằng `flake8`.
  - Thực thi bộ kiểm thử tự động bằng `pytest`.

- **Frontend CI:**
  - Cài đặt dependency sạch bằng `npm ci`.
  - Kiểm tra khả năng build production bằng `npm run build`.

- **Docker Dry-Run:**
  - Build thử nghiệm cả Backend Dockerfile và Frontend Dockerfile.
  - Không push image lên registry.
  - Mục đích là phát hiện sớm lỗi trong quá trình đóng gói môi trường.

- **Branch Protection Rules:**
  - Yêu cầu các bài kiểm tra CI phải đạt trạng thái `passed` trước khi cho phép merge Pull Request vào nhánh chính.

---

### 3.2. Release & Container Publishing (`build-and-publish.yml`)

- **Trigger:**
  - Kích hoạt khi có commit được merge vào nhánh `main`.
  - Hoặc khi tạo Git tag theo semantic versioning dạng `v*.*.*`.

- **Bảo mật:**
  - Xác thực với GitHub Container Registry bằng biến tạm `GITHUB_TOKEN`.
  - Không lưu plaintext credentials trong repository.

- **Tối ưu Build:**
  - Sử dụng Docker Buildx.
  - Sử dụng GitHub Actions Cache (`type=gha`) để tăng tốc quá trình build.

- **Định danh Image:**
  - Tự động gắn các tag:
    - `latest`
    - Short SHA của commit
    - Semantic versioning khi release bằng Git tag.

---

### 3.3. Kéo Container Images từ GHCR

```bash
docker pull ghcr.io/ducanh28807-prog/yolo-web-devops/backend:latest
docker pull ghcr.io/ducanh28807-prog/yolo-web-devops/frontend:latest
```

---

## 4. Hướng dẫn khởi chạy nhanh (Quick Start with Docker)

### 4.1. Yêu cầu môi trường

- **Docker Engine:** 20.10+
- **Docker Compose:** V2

Kiểm tra phiên bản:

```bash
docker --version
docker compose version
```

---

### 4.2. Khởi tạo biến môi trường

Sao chép file `.env.example` thành `.env`:

```bash
cp .env.example .env
```

Sau đó kiểm tra và điều chỉnh các biến môi trường trong `.env` nếu cần.

---

### 4.3. Build và khởi chạy hệ thống

Build và chạy toàn bộ hệ thống bằng một lệnh:

```bash
docker compose up --build -d
```

Kiểm tra trạng thái các container:

```bash
docker compose ps
```

Xem log:

```bash
docker compose logs -f
```

---

### 4.4. Truy cập dịch vụ

Sau khi hệ thống khởi động thành công:

- **Frontend:**

  http://localhost:5173

- **Swagger UI:**

  http://localhost:8000/docs

- **Healthcheck:**

  http://localhost:8000/health

---

### 4.5. Dừng hệ thống

```bash
docker compose down
```

> Lưu ý: `docker compose down` dừng và xóa container/network nhưng dữ liệu trong thư mục `./backend/static` vẫn được giữ lại vì thư mục này được mount từ Docker host.

---

## 5. Danh sách API Endpoints

| Method | Endpoint | Tham số gửi lên (Form-data) | Định dạng trả về | Chức năng |
|---|---|---|---|---|
| **GET** | `/health` | Không có | `application/json` | Kiểm tra trạng thái hoạt động của Backend container |
| **GET** | `/api/results` | Không có | `application/json` | Lấy danh sách ảnh/video kết quả đã lưu trữ trên server |
| **POST** | `/api/detect/image` | `file`: UploadFile<br>`confidence`: float (`0.25`)<br>`save`: bool (`False`) | `image/jpeg` | Nhận diện vật thể trong ảnh; ghi kết quả lâu dài nếu `save=True` |
| **POST** | `/api/detect/video` | `file`: UploadFile<br>`confidence`: float (`0.25`)<br>`save`: bool (`False`) | `video/mp4` | Nhận diện vật thể trong video; tự dọn dẹp file tạm nếu `save=False` |

---

### 5.1. `GET /health`

Dùng để kiểm tra Backend có đang hoạt động hay không.

**Request:**

```http
GET /health
```

**Response:**

```json
{
  "status": "ok"
}
```

---

### 5.2. `GET /api/results`

Trả về danh sách các kết quả đã được lưu trên server.

**Request:**

```http
GET /api/results
```

**Response:**

```json
[
  {
    "filename": "result_xxxxx.jpg",
    "url": "/static/result_xxxxx.jpg"
  }
]
```

---

### 5.3. `POST /api/detect/image`

Nhận diện vật thể trong hình ảnh.

**Form-data:**

| Parameter | Type | Default | Mô tả |
|---|---|---:|---|
| `file` | `UploadFile` | — | File ảnh cần nhận diện |
| `confidence` | `float` | `0.25` | Ngưỡng confidence của YOLO |
| `save` | `bool` | `False` | Có lưu kết quả lâu dài hay không |

**Định dạng hỗ trợ:**

```text
.jpg
.jpeg
.png
```

---

### 5.4. `POST /api/detect/video`

Nhận diện vật thể trong video.

**Form-data:**

| Parameter | Type | Default | Mô tả |
|---|---|---:|---|
| `file` | `UploadFile` | — | File video cần nhận diện |
| `confidence` | `float` | `0.25` | Ngưỡng confidence của YOLO |
| `save` | `bool` | `False` | Có lưu kết quả lâu dài hay không |

**Định dạng hỗ trợ:**

```text
.mp4
```

---

## 6. Quy chuẩn kiểm tra dữ liệu & Quản lý file tạm

### 6.1. Ràng buộc đầu vào

#### Định dạng file

**Ảnh:**

```text
.jpg
.jpeg
.png
```

**Video:**

```text
.mp4
```

#### Giới hạn dung lượng

Dung lượng file upload tối đa:

```text
50 MB
```

---

### 6.2. Mã lỗi phản hồi chuẩn REST

| HTTP Status | Ý nghĩa | Trường hợp |
|---|---|---|
| `400 Bad Request` | Request không hợp lệ | File rỗng hoặc không thể giải mã bằng OpenCV |
| `413 Request Entity Too Large` | File quá lớn | Dung lượng vượt quá 50 MB |
| `415 Unsupported Media Type` | Sai định dạng | File không thuộc định dạng được hỗ trợ |
| `500 Internal Server Error` | Lỗi server | Lỗi phát sinh trong quá trình inference hoặc xử lý frame |

---

### 6.3. Cơ chế lưu trữ & dọn dẹp

Hệ thống phân biệt rõ giữa **file tạm** và **file kết quả cần lưu trữ lâu dài**.

#### File tạm

Các file tạm phát sinh trong quá trình xử lý bao gồm:

- Video input được upload.
- File raw/intermediate `mp4v`.
- Các file trung gian phục vụ quá trình xử lý video.

Các file này được tự động xóa sau khi hoàn thành tác vụ.

#### Khi `save=False`

Kết quả video không được lưu trữ lâu dài.

Sau khi kết quả được truyền hoàn tất đến client, hệ thống sử dụng **FastAPI `BackgroundTasks`** để tự động dọn dẹp file kết quả.

Luồng xử lý:

```text
Upload
   │
   ▼
Temporary File
   │
   ▼
YOLOv8 Inference
   │
   ▼
Result File
   │
   ▼
Truyền kết quả cho Client
   │
   ▼
BackgroundTasks
   │
   ▼
Xóa file tạm
```

#### Khi `save=True`

Kết quả được lưu bền vững trong:

```text
./backend/static
```

Thư mục này được mount vào container thông qua Docker volume/bind mount.

Do đó, dữ liệu không phụ thuộc vào vòng đời của container.

```text
Docker Container
       │
       │ mount
       ▼
./backend/static
       │
       ▼
Docker Host
```

Khi thực hiện:

```bash
docker compose down
```

container và network bị xóa nhưng dữ liệu trong `./backend/static` vẫn được giữ lại.

---

## 7. Kiểm thử tự động (Automated Tests)

Backend được trang bị bộ kiểm thử tự động sử dụng **pytest** nhằm kiểm tra tính toàn vẹn của API.

### 7.1. Chạy test trong container

```bash
docker exec -it yolo-backend-app pytest test_main.py -v
```

### 7.2. Kết quả mong đợi

Các test case phải hoàn thành với trạng thái:

```text
PASSED
```

Ví dụ:

```text
======================== test session starts ========================

test_main.py::test_xxxxx PASSED
test_main.py::test_xxxxx PASSED
test_main.py::test_xxxxx PASSED

========================= ... passed ================================
```

---

## 8. Docker Architecture

Hệ thống được đóng gói thành các container độc lập:

```text
                    ┌──────────────────────┐
                    │      Web Browser     │
                    │        Client        │
                    └──────────┬───────────┘
                               │
                               │ :5173
                               ▼
                    ┌──────────────────────┐
                    │ Frontend Container   │
                    │ React + Vite + Nginx │
                    └──────────┬───────────┘
                               │
                               │ Docker Network
                               │   yolo-net
                               ▼
                    ┌──────────────────────┐
                    │ Backend Container    │
                    │ FastAPI + YOLOv8     │
                    │ Python / OpenCV      │
                    └──────────┬───────────┘
                               │
                               │ Mount
                               ▼
                    ┌──────────────────────┐
                    │    Host Storage      │
                    │ ./backend/static     │
                    └──────────────────────┘
```

### Frontend Container

Frontend sử dụng **multi-stage Docker build**:

```text
Node 20
   │
   │ npm ci
   │ npm run build
   ▼
Production Build
   │
   ▼
Nginx Alpine
   │
   ▼
Static Web Application
```

### Backend Container

Backend chạy:

```text
FastAPI
   │
   ▼
YOLOv8
   │
   ▼
OpenCV
   │
   ▼
Image / Video Result
```

Backend container sử dụng user không có quyền `root` để giảm quyền hạn trong runtime.

---

## 9. GitHub Container Registry (GHCR)

Docker images sau khi được build thành công sẽ được publish lên:

```text
GitHub Container Registry
        │
        ├── backend:latest
        └── frontend:latest
```

Pull image:

```bash
docker pull ghcr.io/ducanh28807-prog/yolo-web-devops/backend:latest

docker pull ghcr.io/ducanh28807-prog/yolo-web-devops/frontend:latest
```

Sau đó có thể kiểm tra image:

```bash
docker images
```

---

## 10. Git Workflow

Quy trình phát triển sử dụng Pull Request để kiểm soát chất lượng code trước khi merge vào `main`.

```text
Developer
    │
    ▼
feature branch
    │
    ▼
Commit / Push
    │
    ▼
Pull Request
    │
    ▼
GitHub Actions CI
    │
    ├── Flake8
    ├── Pytest
    ├── Frontend Build
    └── Docker Build
            │
            ▼
       All Passed
            │
            ▼
       Merge → main
            │
            ▼
     Release Workflow
            │
            ▼
          GHCR
```

---

## 11. Giới hạn kỹ thuật (Limitations)

### 11.1. Xử lý video tải cao

Quá trình nhận diện video hiện được xử lý đồng bộ theo request.

Hệ thống chưa tích hợp:

- Celery
- Redis Queue
- Message Broker
- Distributed Worker

Do đó, khi có nhiều request video lớn cùng lúc, tài nguyên CPU và thời gian xử lý có thể trở thành bottleneck.

---

### 11.2. Môi trường suy luận

Mô hình YOLOv8 hiện thực thi trên **CPU**.

Hệ thống chưa tích hợp:

```text
NVIDIA GPU
CUDA
cuDNN
GPU inference
```

Vì vậy hiệu năng inference video phụ thuộc đáng kể vào năng lực CPU của máy chủ.

---

## 12. Tổng kết

Project cung cấp một pipeline hoàn chỉnh từ phát triển đến triển khai:

```text
Source Code
     │
     ▼
Git / GitHub
     │
     ▼
Pull Request
     │
     ▼
GitHub Actions CI
     │
     ├── Lint
     ├── Pytest
     ├── Frontend Build
     └── Docker Build
             │
             ▼
        Merge to main
             │
             ▼
 GitHub Actions Release
             │
             ▼
 Docker Buildx + Cache
             │
             ▼
            GHCR
             │
             ▼
       Docker Images
             │
             ▼
      Docker Compose
             │
       ┌─────┴─────┐
       ▼           ▼
   Frontend     Backend
    Nginx      FastAPI
                 │
                 ▼
               YOLOv8
                 │
                 ▼
             Host Volume
```

Hệ thống đáp ứng các thành phần chính của Week 4:

- Docker containerization.
- Docker Compose orchestration.
- Persistent storage bằng Volume.
- Healthcheck.
- Automated testing với Pytest.
- Code quality checking với Flake8.
- Frontend production build.
- Docker build validation.
- GitHub Actions CI/CD.
- GitHub Container Registry.
- Docker Buildx Cache.
- Secure authentication bằng `GITHUB_TOKEN`.
- Pull Request verification.
- Branch protection.
- Tự động cleanup file tạm.
