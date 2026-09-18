import os
import shutil
import subprocess
import uuid
import cv2
import numpy as np
import time
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from ultralytics import YOLO

app = FastAPI(title="YOLO Object Detection API")

# Cấu hình CORS để Frontend (Vite cổng 5173) gọi được Backend (cổng 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],  # <--- [THÊM DÒNG NÀY]: BẮT BUỘC!
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Tải mô hình YOLOv8n
model = YOLO("yolov8n.pt")
MAX_FILE_SIZE = 50 * 1024 * 1024  # Tối đa 50MB


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# 1. ENDPOINT NHẬN DIỆN ẢNH
@app.post("/api/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    confidence: float = Form(0.25)
):

    start_time = time.perf_counter()
    
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Chỉ chấp nhận file ảnh JPG hoặc PNG."
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Kích thước ảnh vượt quá giới hạn."
        )

    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể đọc nội dung ảnh."
        )

    # Chạy YOLO nhận diện với ngưỡng confidence nhận từ frontend
    results = model.predict(img, conf=confidence)
    annotated_frame = results[0].plot()

    # Nén frame đã vẽ hộp sang JPEG nhị phân
    success, encoded_image = cv2.imencode(".jpg", annotated_frame)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi trích xuất ảnh kết quả."
        )

    process_time = (time.perf_counter() - start_time) * 1000  # Đổi ra mili-giây (ms)
    headers = {"X-Process-Time": f"{process_time:.1f}ms"}

    # <--- [SỬA LẠI DÒNG RETURN]: Thêm tham số headers=headers
    return Response(
        content=encoded_image.tobytes(), 
        media_type="image/jpeg", 
        headers=headers
    )


# 2. ENDPOINT NHẬN DIỆN VIDEO (Dùng def thường để đẩy sang ThreadPool riêng)
@app.post("/api/detect/video")
def detect_video(
    file: UploadFile = File(...),
    confidence: float = Form(0.25)
):
    start_time = time.perf_counter()  # <--- [THÊM VÀO ĐẦU HÀM]: Bắt đầu bấm giờ
    
    if file.content_type not in ["video/mp4"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Chỉ chấp nhận file video định dạng MP4."
        )

    session_id = str(uuid.uuid4())[:8]
    temp_input_path = os.path.join(STATIC_DIR, f"input_{session_id}_{file.filename}")
    raw_output_path = os.path.join(STATIC_DIR, f"raw_{session_id}_{file.filename}")
    final_output_filename = f"output_{session_id}_{file.filename}"
    final_output_path = os.path.join(STATIC_DIR, final_output_filename)

    # Lưu file video nhận được vào đĩa
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cap = cv2.VideoCapture(temp_input_path)
    if not cap.isOpened():
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể mở file video."
        )

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    # Dùng mp4v để OpenCV ghi tạm ổn định trên Linux
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(raw_output_path, fourcc, fps, (width, height))

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = model.predict(frame, conf=confidence, verbose=False)
            annotated_frame = results[0].plot()
            out.write(annotated_frame)
    finally:
        # Bắt buộc đóng cả 2 luồng để hoàn thiện cấu trúc file
        cap.release()
        out.release()
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)

    # Dùng FFmpeg chuyển sang chuẩn H.264 + yuv420p + faststart để Chrome phát được
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", raw_output_path,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        final_output_path
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Xóa file raw trung gian
    if os.path.exists(raw_output_path):
        os.remove(raw_output_path)

    process_time = time.perf_counter() - start_time  # Video chạy lâu nên để đơn vị giây (s)
    headers = {"X-Process-Time": f"{process_time:.2f}s"}

    # <--- [SỬA LẠI DÒNG RETURN]: Thêm tham số headers=headers
    return FileResponse(
        final_output_path,
        media_type="video/mp4",
        filename=final_output_filename,
        headers=headers
    )
