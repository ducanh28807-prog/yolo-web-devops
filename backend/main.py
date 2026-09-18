import os
import shutil
import subprocess
import uuid
import cv2
import numpy as np
import time
import glob
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO

app = FastAPI(title="YOLO Object Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# [MỚI 1]: Mount thư mục static để Frontend có thể xem lại file qua URL
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

model = YOLO("yolov8n.pt")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# [MỚI 2]: Hàm hỗ trợ dọn rác file tạm
def remove_file(path: str):
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            print(f"Lỗi khi xóa file tạm {path}: {e}")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# [MỚI 3]: API lấy danh sách các file đã được yêu cầu lưu lại (đáp ứng tính năng xem lại)
@app.get("/api/results")
def get_saved_results():
    pattern = os.path.join(STATIC_DIR, "*.*")
    files = glob.glob(pattern)
    files.sort(key=os.path.getmtime, reverse=True)
    
    results = []
    for f in files:
        fname = os.path.basename(f)
        # Chỉ hiển thị các file kết quả (đã gán nhãn), bỏ qua các file input tạm nếu còn sót
        if fname.startswith("result_"):
            results.append({
                "filename": fname,
                "url": f"http://localhost:8000/static/{fname}",
                "type": "video" if fname.endswith(".mp4") else "image",
                "created_at": datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
            })
    return results


# 1. ENDPOINT NHẬN DIỆN ẢNH
@app.post("/api/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    confidence: float = Form(0.25),
    save: bool = Form(False)  # <--- [MỚI]: Nhận cờ save (mặc định False)
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

    results = model.predict(img, conf=confidence)
    annotated_frame = results[0].plot()

    # [MỚI]: Nếu người dùng yêu cầu (save=True) -> Mới lưu vào ổ cứng tĩnh
    if save:
        session_id = str(uuid.uuid4())[:8]
        save_path = os.path.join(STATIC_DIR, f"result_{session_id}_{file.filename}")
        cv2.imwrite(save_path, annotated_frame)

    success, encoded_image = cv2.imencode(".jpg", annotated_frame)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi trích xuất ảnh kết quả."
        )

    process_time = (time.perf_counter() - start_time) * 1000
    headers = {"X-Process-Time": f"{process_time:.1f}ms"}

    return Response(
        content=encoded_image.tobytes(), 
        media_type="image/jpeg", 
        headers=headers
    )


# 2. ENDPOINT NHẬN DIỆN VIDEO
@app.post("/api/detect/video")
def detect_video(
    background_tasks: BackgroundTasks,  # <--- [MỚI]: Inject tác vụ ngầm
    file: UploadFile = File(...),
    confidence: float = Form(0.25),
    save: bool = Form(False)            # <--- [MỚI]: Nhận cờ save (mặc định False)
):
    start_time = time.perf_counter()
    
    if file.content_type not in ["video/mp4"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Chỉ chấp nhận file video định dạng MP4."
        )

    session_id = str(uuid.uuid4())[:8]
    temp_input_path = os.path.join(STATIC_DIR, f"temp_in_{session_id}_{file.filename}")
    raw_output_path = os.path.join(STATIC_DIR, f"temp_raw_{session_id}_{file.filename}")
    
    # Nếu save=True thì đặt tên tiền tố "result_" để API /api/results nhận diện; nếu không thì đặt temp_
    prefix = "result_" if save else "temp_out_"
    final_output_filename = f"{prefix}{session_id}_{file.filename}"
    final_output_path = os.path.join(STATIC_DIR, final_output_filename)

    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cap = cv2.VideoCapture(temp_input_path)
    if not cap.isOpened():
        remove_file(temp_input_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể mở file video."
        )

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

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
        cap.release()
        out.release()
        # [DỌN FILE TẠM 1]: Xóa ngay file input sau khi render xong
        remove_file(temp_input_path)

    # Chuyển mã H.264
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", raw_output_path,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        final_output_path
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # [DỌN FILE TẠM 2]: Xóa ngay file raw mp4v
    remove_file(raw_output_path)

    # [QUAN TRỌNG NHẤT - TIÊU CHÍ CLEAN TEMPORARY FILES]:
    # Nếu người dùng KHÔNG yêu cầu lưu (save=False):
    # Đăng ký background task để sau khi truyền xong video tới client thì tự động xóa file trên đĩa
    if not save:
        background_tasks.add_task(remove_file, final_output_path)

    process_time = time.perf_counter() - start_time
    headers = {"X-Process-Time": f"{process_time:.2f}s"}

    return FileResponse(
        final_output_path,
        media_type="video/mp4",
        filename=final_output_filename,
        headers=headers,
        background=background_tasks if not save else None
    )
