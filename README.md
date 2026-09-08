# YOLO Object Detection Web Application (Week 2 Milestone)

Dự án ứng dụng web nhận diện vật thể trong hình ảnh và video ngắn sử dụng mô hình pre-trained YOLOv8 (Ultralytics), kết hợp **FastAPI** (Backend) và **React + Vite** (Frontend).

---

## 1. Luồng xử lý của hệ thống (Request Flow)

Hệ thống hoạt động theo chu trình khép kín giữa client và server:
```text
Trình duyệt ──► Frontend (React + Vite) ──► API (FastAPI) ──► YOLOv8 Model
     ▲                                                               │
     └──────────────── Trả về kết quả (Ảnh / Video gán nhãn) ────────┘
```

---

## 2. Cấu trúc thư mục dự án (Project Structure)

Dự án được tổ chức theo cấu trúc monorepo tinh giản, loại trừ các thư mục sinh ra trong quá trình chạy (runtime):

```text
.
├── backend/
│   ├── main.py              # Toàn bộ mã nguồn API FastAPI, nạp YOLOv8 và xử lý ảnh/video
│   ├── test_main.py         # Bộ 3 ca kiểm thử tự động (pytest)
│   └── requirements.txt     # Danh sách thư viện Python cần cài đặt
├── frontend/
│   ├── src/                 # Mã nguồn React (App.jsx, components giao diện)
│   ├── index.html           # Template trang tĩnh cho Vite
│   ├── package.json         # Danh sách dependencies & script npm
│   └── vite.config.js       # File cấu hình Vite
└── README.md
```

> **Lưu ý:** Thư mục tạm `backend/static/` sẽ được máy chủ tự động khởi tạo khi chạy để xử lý các file video và tự động dọn dẹp sau khi hoàn tất.

---

## 3. Hướng dẫn cài đặt và khởi chạy cục bộ (Local Setup)

### Yêu cầu môi trường
* **Python:** 3.10 trở lên
* **Node.js:** 18.x trở lên kèm `npm`
* **Trình duyệt web:** Google Chrome, Microsoft Edge hoặc Firefox

---

### Bước 1: Khởi động Backend (FastAPI)

1. Mở terminal và chuyển vào thư mục `backend`:
   ```bash
   cd backend
   ```

2. Tạo và kích hoạt môi trường ảo:
   * **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   * **Windows:**
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```

3. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Khởi chạy máy chủ API:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   * Mô hình `yolov8n.pt` được nạp sẵn vào bộ nhớ một lần duy nhất khi khởi động.
   * Server mở và lắng nghe tại cổng **`8000`** (`http://localhost:8000`).

---

### Bước 2: Khởi động Frontend (React + Vite)

1. Mở một terminal mới và chuyển vào thư mục `frontend`:
   ```bash
   cd frontend
   ```

2. Cài đặt các gói thư viện phụ thuộc:
   ```bash
   npm install
   ```

3. Khởi chạy máy chủ phát triển Vite:
   ```bash
   npm run dev
   ```
   * Truy cập giao diện tại: `http://localhost:5173`.

---

## 4. Danh sách API Endpoints

Kiểm thử tài liệu API tương tác tự động (Swagger UI) tại:  
👉 **`http://localhost:8000/docs`**

| Method | Endpoint | Tham số gửi lên (Form-data) | Định dạng phản hồi | Chức năng |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/health` | Không có | `application/json` | Kiểm tra trạng thái máy chủ (phục vụ health check cho Docker sau này). |
| **POST** | `/api/detect/image` | `file`: UploadFile (Ảnh)<br>`confidence`: float (mặc định `0.25`) | `image/jpeg` | Nhận diện vật thể trên ảnh tĩnh và trả về trực tiếp ảnh đã vẽ bounding box. |
| **POST** | `/api/detect/video` | `file`: UploadFile (Video clip)<br>`confidence`: float (mặc định `0.25`) | `video/mp4` | Đọc từng frame video, nhận diện và xuất tệp video MP4 hoàn chỉnh. |

---

## 5. Định dạng hỗ trợ & Quy chuẩn kiểm tra (Validation & Errors)

Hệ thống kiểm soát tính toàn vẹn của tệp tải lên và xử lý lỗi chặt chẽ:

* **Định dạng file cho phép:**
  * **Ảnh tĩnh:** `.jpg`, `.jpeg`, `.png`.
  * **Video:** `.mp4` (đoạn clip ngắn).
  * **Giới hạn dung lượng:** Tối đa `10MB` (`MAX_FILE_SIZE = 10 * 1024 * 1024 bytes`).
* **Quy chuẩn mã lỗi phản hồi:**
  * `415 Unsupported Media Type`: File tải lên sai định dạng yêu cầu.
  * `413 Request Entity Too Large`: Dung lượng file vượt quá giới hạn 10MB.
  * `400 Bad Request`: Không thể giải mã tệp ảnh bằng OpenCV hoặc video bị lỗi cấu trúc.
  * `500 Internal Server Error`: Lỗi phát sinh trong quá trình mã hóa xuất ảnh kết quả.
* **Cấu hình CORS:** Kích hoạt `CORSMiddleware` với `allow_origins=["*"]` cho phép ứng dụng React kết nối linh hoạt mà không bị chặn bởi chính sách cùng nguồn của trình duyệt.

---

## 6. Tính năng giao diện Frontend (React + Vite)

Ứng dụng Single Page Application (React) đáp ứng đầy đủ các yêu cầu giao diện:
* **Tải lên & Xem trước (Upload & Preview):** Chọn ảnh/video và hiển thị bản xem trước trực tiếp trên màn hình.
* **Thanh trượt ngưỡng tin cậy (Confidence Slider):** Điều chỉnh linh hoạt tham số `confidence` từ `0.05` đến `0.95` trước khi thực hiện nhận diện.
* **Trạng thái giao diện:**
  * **Loading state:** Hiển thị thông báo/spinner đang xử lý và vô hiệu hóa nút bấm trong quá trình nhận diện.
  * **Error state:** Báo lỗi trực quan khi file vượt quá kích thước hoặc Backend trả về mã lỗi `4xx/5xx`.
* **Khu vực hiển thị kết quả (Result View):** Hiển thị trực tiếp ảnh hoặc phát video kết quả đã vẽ khung nhận diện (bounding box).

---

## 7. Kiểm thử tự động Backend (Automated Tests)

Hệ thống tích hợp bộ kiểm thử tự động sử dụng `pytest` với tối thiểu 3 ca kiểm thử theo tiêu chí nghiệm thu:
1. `test_health_check`: Kiểm tra endpoint `/health` trả về mã `200 OK` và status `healthy`.
2. `test_detect_image_valid`: Tải lên ảnh hợp lệ, xác nhận server trả về status `200` kèm định dạng `image/jpeg`.
3. `test_detect_invalid_file_format`: Tải lên file sai định dạng (ví dụ `.txt`), xác nhận server từ chối an toàn với mã lỗi `415 Unsupported Media Type`.

**Lệnh thực thi kiểm thử:**
Tại thư mục `backend/` (đang bật môi trường ảo):
```bash
pytest test_main.py -v
```

---

## 8. Giới hạn kỹ thuật (Limitations)

Dự án tuần 2 tuân thủ tiêu chí thiết kế tinh giản:
1. **Chưa có Database:** Metadata và kết quả nhận diện không lưu trữ vĩnh viễn.
2. **Không có hệ thống xác thực (No Authentication):** API mở truy cập công khai.
3. **Mô hình Pre-trained cố định:** Sử dụng trực tiếp `yolov8n.pt` trên 80 lớp COCO, không huấn luyện lại mô hình tùy biến.
4. **Xử lý đồng bộ trên CPU:** Xử lý video tuần tự trên tài nguyên máy chủ cục bộ, chỉ phù hợp cho các đoạn clip ngắn (dưới 15–30 giây) do chưa áp dụng hàng đợi tác vụ nền (Task Queue).

---

## 9. Minh chứng kết quả (Screenshots)

*(Lưu ảnh chụp màn hình kiểm thử thực tế vào thư mục `docs/screenshots/`)*

* **Tài liệu Swagger UI tương tác (`/docs`):**  
  ![Swagger UI](docs/screenshots/swagger_docs.png)

* **Giao diện nhận diện ảnh:**  
  ![Image Detection](docs/screenshots/image_result.png)

* **Giao diện nhận diện video clip:**  
  ![Video Detection](docs/screenshots/video_result.png)

* **Kết quả bộ kiểm thử tự động pytest (Pass 3/3):**  
  ![Pytest Results](docs/screenshots/pytest_results.png)
