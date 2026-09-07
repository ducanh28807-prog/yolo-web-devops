import os
import shutil
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from ultralytics import YOLO

app = FastAPI(title="YOLO Object Detection API")

# Cấu hình CORS cho phép cả cổng Vite và Live Server / file cục bộ truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mở cho mọi port trong giai đoạn phát triển nội bộ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo thư mục static và load mô hình YOLOv8 nano
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

model = YOLO("yolov8n.pt")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# 2. Endpoint kiểm tra trạng thái
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# 3. Endpoint nhận diện ảnh
@app.post("/api/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    confidence: float = Form(0.25)
):
    # Kiểm tra định dạng file (Lỗi 415: Unsupported Media Type)
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Chỉ chấp nhận file ảnh định dạng JPG hoặc PNG."
        )

    # Đọc dữ liệu và kiểm tra dung lượng (Lỗi 413: Request Entity Too Large)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Dung lượng file vượt quá giới hạn 10MB."
        )

    # Chuyển đổi byte sang định dạng ảnh OpenCV
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể đọc nội dung ảnh tải lên."
        )

    # Chạy mô hình YOLO
    results = model.predict(img, conf=confidence)
    annotated_frame = results[0].plot()

    # Mã hóa ảnh kết quả sang định dạng JPEG để trả về trực tiếp
    success, encoded_image = cv2.imencode(".jpg", annotated_frame)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi xử lý xuất ảnh kết quả."
        )

    return Response(content=encoded_image.tobytes(), media_type="image/jpeg")


# 4. Endpoint nhận diện video MP4
@app.post("/api/detect/video")
async def detect_video(
    file: UploadFile = File(...),
    confidence: float = Form(0.25)
):
    if file.content_type not in ["video/mp4"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Chỉ chấp nhận file video định dạng MP4."
        )

    # Lưu file video tải lên vào thư mục static
    temp_input_path = os.path.join(STATIC_DIR, f"input_{file.filename}")
    output_filename = f"output_{file.filename}"
    temp_output_path = os.path.join(STATIC_DIR, output_filename)

    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Đọc video bằng OpenCV
    cap = cv2.VideoCapture(temp_input_path)
    if not cap.isOpened():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể mở file video."
        )

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    # Khởi tạo VideoWriter (sử dụng codec mp4v)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))

    # Lặp qua từng frame để phát hiện vật thể và vẽ bounding box
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=confidence, verbose=False)
        annotated_frame = results[0].plot()
        out.write(annotated_frame)

    cap.release()
    out.release()

    # Dọn dẹp file video gốc
    if os.path.exists(temp_input_path):
        os.remove(temp_input_path)

    return FileResponse(
        temp_output_path,
        media_type="video/mp4",
        filename=output_filename
    )

