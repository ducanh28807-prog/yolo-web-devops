# Nhập thư viện thao tác với hệ thống tệp và đường dẫn
import os
# Nhập thư viện sao chép file luồng dữ liệu lớn
import shutil
# Nhập thư viện gọi tiến trình con của hệ điều hành thực thi FFmpeg
import subprocess
# Nhập thư viện tạo chuỗi định danh ngẫu nhiên duy nhất
import uuid
# Nhập thư viện OpenCV xử lý ma trận ảnh và video
import cv2
# Nhập thư viện NumPy xử lý mảng dữ liệu byte
import numpy as np
# Nhập thư viện tính toán thời gian xử lý dữ liệu
import time
# Nhập thư viện tìm kiếm file theo mẫu đường dẫn
import glob
# Nhập thư viện định dạng thời gian thực tế
from datetime import datetime
# Nhập các thành phần cốt lõi của framework FastAPI
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status, BackgroundTasks
# Nhập middleware hỗ trợ chia sẻ tài nguyên CORS
from fastapi.middleware.cors import CORSMiddleware
# Nhập các lớp phản hồi nhị phân và phản hồi file vật lý
from fastapi.responses import Response, FileResponse
# Nhập module hỗ trợ mount thư mục tĩnh phục vụ qua giao thức HTTP
from fastapi.staticfiles import StaticFiles
# Nhập lớp YOLO từ thư viện Ultralytics
from ultralytics import YOLO

# Khởi tạo đối tượng ứng dụng FastAPI
app = FastAPI(title="YOLO Object Detection API")

# Cấu hình middleware CORS cho phép các kết nối web
app.add_middleware(
    CORSMiddleware,
    # Cho phép mọi nguồn gốc gửi request
    allow_origins=["*"],
    # Hỗ trợ đính kèm cookie và thông tin chứng thực
    allow_credentials=True,
    # Chấp nhận mọi phương thức HTTP
    allow_methods=["*"],
    # Chấp nhận mọi header trong request
    allow_headers=["*"],
    # Cho phép client đọc header tùy biến X-Process-Time
    expose_headers=["X-Process-Time"],
)

# Thiết lập đường dẫn tuyệt đối trỏ tới thư mục static
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
# Tự động tạo thư mục static nếu chưa tồn tại
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount thư mục static vào router dưới tiền tố /static
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Nạp sẵn mô hình nhận diện YOLOv8 phiên bản nano vào bộ nhớ
model = YOLO("yolov8n.pt")
# Quy định giới hạn kích thước file tối đa là 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


# Hàm tiện ích dọn dẹp file vật lý trên ổ đĩa
def remove_file(path: str):
    # Kiểm tra xem đường dẫn file có tồn tại thật không
    if os.path.exists(path):
        try:
            # Tiến hành xóa file khỏi hệ thống
            os.remove(path)
        except Exception as e:
            # Ghi thông báo ra console nếu xảy ra lỗi trong quá trình xóa file
            print(f"Lỗi khi xóa file tạm {path}: {e}")


# Endpoint phục vụ việc kiểm tra trạng thái hoạt động của container
@app.get("/health")
def health_check():
    # Trả về mã JSON thông báo trạng thái sẵn sàng
    return {"status": "healthy"}


# Endpoint cung cấp danh sách các file kết quả đã được lưu lại
@app.get("/api/results")
def get_saved_results():
    # Định nghĩa mẫu quét tìm kiếm toàn bộ file trong thư mục static
    pattern = os.path.join(STATIC_DIR, "*.*")
    # Lấy danh sách toàn bộ đường dẫn các file thỏa mãn mẫu quét
    files = glob.glob(pattern)
    # Sắp xếp các file theo thứ tự thời gian sửa đổi mới nhất lên đầu
    files.sort(key=os.path.getmtime, reverse=True)
    
    # Khởi tạo danh sách kết quả trả về
    results = []
    # Lặp qua từng file trong danh sách đã quét
    for f in files:
        # Lấy tên file kèm phần mở rộng
        fname = os.path.basename(f)
        # Chỉ chọn các file là kết quả nhận diện có tiền tố result_
        if fname.startswith("result_"):
            # Bổ sung thông tin chi tiết của file vào danh sách trả về
            results.append({
                # Tên file kết quả
                "filename": fname,
                # Đường dẫn tương đối phục vụ qua Reverse Proxy (không gán cứng host/port)
                "url": f"/static/{fname}",
                # Nhận diện kiểu tệp là video nếu đuôi là mp4, ngược lại là ảnh
                "type": "video" if fname.endswith(".mp4") else "image",
                # Chuyển đổi timestamp sang chuỗi ngày giờ dễ đọc
                "created_at": datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
            })
    # Trả về danh sách kết quả dưới dạng JSON
    return results


# Endpoint tiếp nhận và thực hiện nhận diện trên tệp hình ảnh
@app.post("/api/detect/image")
async def detect_image(
    # Tiếp nhận file ảnh tải lên từ form-data
    file: UploadFile = File(...),
    # Tiếp nhận ngưỡng tin cậy nhận diện với giá trị mặc định 0.25
    confidence: float = Form(0.25),
    # Tiếp nhận cờ lưu trữ kết quả với giá trị mặc định False
    save: bool = Form(False)
):
    # Bắt đầu bấm giờ đo thời gian xử lý
    start_time = time.perf_counter()
    
    # Kiểm tra tính hợp lệ của định dạng mime type ảnh
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        # Ném lỗi 415 nếu định dạng file không được hỗ trợ
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Chỉ chấp nhận file ảnh JPG hoặc PNG."
        )

    # Đọc luồng byte dữ liệu từ file ảnh vào bộ nhớ
    contents = await file.read()
    # Kiểm tra nếu dung lượng ảnh vượt quá ngưỡng quy định 50MB
    if len(contents) > MAX_FILE_SIZE:
        # Ném lỗi 413 nếu dung lượng file quá lớn
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Kích thước ảnh vượt quá giới hạn."
        )

    # Chuyển đổi chuỗi byte ảnh thành mảng dữ liệu 1 chiều dạng số nguyên uint8
    nparr = np.frombuffer(contents, np.uint8)
    # Dùng OpenCV giải mã mảng dữ liệu thành ma trận màu BGR
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Kiểm tra xem OpenCV có giải mã thành công file ảnh không
    if img is None:
        # Ném lỗi 400 nếu file ảnh bị lỗi cấu trúc dữ liệu
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể đọc nội dung ảnh."
        )

    # Đưa ma trận ảnh vào mô hình YOLOv8 để thực hiện nhận diện
    results = model.predict(img, conf=confidence)
    # Vẽ các bounding box và nhãn nhận diện đè lên ảnh gốc
    annotated_frame = results[0].plot()

    # Kiểm tra nếu người dùng yêu cầu lưu kết quả vào thư mục tĩnh
    if save:
        # Tạo chuỗi định danh ngẫu nhiên 8 ký tự
        session_id = str(uuid.uuid4())[:8]
        # Xây dựng đường dẫn file lưu trữ lâu dài trong thư mục static
        save_path = os.path.join(STATIC_DIR, f"result_{session_id}_{file.filename}")
        # Dùng OpenCV lưu ma trận ảnh đã vẽ nhãn xuống đĩa
        cv2.imwrite(save_path, annotated_frame)

    # Nén ảnh đã nhận diện thành dữ liệu định dạng JPG trong RAM
    success, encoded_image = cv2.imencode(".jpg", annotated_frame)
    # Kiểm tra xem việc mã hóa nén ảnh có thành công không
    if not success:
        # Ném lỗi 500 nếu xảy ra sự cố trong quá trình nén ảnh
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi trích xuất ảnh kết quả."
        )

    # Tính toán tổng thời gian xử lý và quy đổi ra mili-giây
    process_time = (time.perf_counter() - start_time) * 1000
    # Đóng gói thời gian xử lý vào custom header
    headers = {"X-Process-Time": f"{process_time:.1f}ms"}

    # Trả trực tiếp dữ liệu nhị phân của bức ảnh về cho trình duyệt hiển thị
    return Response(
        content=encoded_image.tobytes(),
        media_type="image/jpeg",
        headers=headers
    )


# Endpoint tiếp nhận và thực hiện nhận diện trên tệp video
@app.post("/api/detect/video")
def detect_video(
    # Khai báo tác vụ nền để thực thi việc xóa file sau khi truyền dữ liệu
    background_tasks: BackgroundTasks,
    # Tiếp nhận file video tải lên từ form-data
    file: UploadFile = File(...),
    # Tiếp nhận ngưỡng tin cậy nhận diện
    confidence: float = Form(0.25),
    # Tiếp nhận cờ lưu trữ kết quả lâu dài
    save: bool = Form(False)
):
    # Bắt đầu bấm giờ đo thời gian xử lý video
    start_time = time.perf_counter()
    
    # Kiểm tra tính hợp lệ của định dạng mime type video
    if file.content_type not in ["video/mp4"]:
        # Ném lỗi 415 nếu không phải định dạng MP4
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Chỉ chấp nhận file video định dạng MP4."
        )

    # Sinh mã phiên làm việc ngẫu nhiên 8 ký tự
    session_id = str(uuid.uuid4())[:8]
    # Đường dẫn lưu trữ tạm tệp video đầu vào
    temp_input_path = os.path.join(STATIC_DIR, f"temp_in_{session_id}_{file.filename}")
    # Đường dẫn lưu trữ tạm tệp video thô được xuất từ OpenCV
    raw_output_path = os.path.join(STATIC_DIR, f"temp_raw_{session_id}_{file.filename}")
    
    # Phân loại tiền tố tên file tùy thuộc vào người dùng có chọn lưu hay không
    prefix = "result_" if save else "temp_out_"
    # Đặt tên cho file video đầu ra hoàn chỉnh
    final_output_filename = f"{prefix}{session_id}_{file.filename}"
    # Xác định đường dẫn tuyệt đối cho file video thành phẩm cuối cùng
    final_output_path = os.path.join(STATIC_DIR, final_output_filename)

    # Ghi nội dung file video gửi lên vào file tạm trên đĩa
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Mở luồng đọc video tạm bằng OpenCV VideoCapture
    cap = cv2.VideoCapture(temp_input_path)
    # Kiểm tra xem luồng đọc video có mở thành công không
    if not cap.isOpened():
        # Xóa ngay file tạm nếu video không đọc được
        remove_file(temp_input_path)
        # Ném lỗi 400 thông báo file video bị lỗi
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể mở file video."
        )

    # Đọc thông số chiều rộng khung hình gốc
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    # Đọc thông số chiều cao khung hình gốc
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # Đọc tốc độ khung hình (FPS) gốc, mặc định gán 25.0 nếu không đọc được
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    # Khởi tạo định dạng FourCC chuẩn mp4v cho luồng ghi video thô
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    # Khởi tạo đối tượng ghi video thô với các thông số kích thước và FPS tương ứng
    out = cv2.VideoWriter(raw_output_path, fourcc, fps, (width, height))

    try:
        # Vòng lặp đọc và xử lý từng khung hình của video
        while cap.isOpened():
            # Đọc khung hình kế tiếp
            ret, frame = cap.read()
            # Dừng vòng lặp khi đã đọc hết các khung hình
            if not ret:
                break
            # Thực hiện nhận diện vật thể trên khung hình mà không in log
            results = model.predict(frame, conf=confidence, verbose=False)
            # Vẽ bounding box nhận diện lên khung hình
            annotated_frame = results[0].plot()
            # Ghi khung hình đã vẽ nhãn vào file video thô
            out.write(annotated_frame)
    finally:
        # Giải phóng tài nguyên đối tượng đọc video
        cap.release()
        # Đóng đối tượng ghi video thô
        out.release()
        # Xóa ngay file video đầu vào tạm để tiết kiệm dung lượng đĩa
        remove_file(temp_input_path)

    # Cấu hình danh sách lệnh chuyển mã video sang chuẩn H.264 qua công cụ FFmpeg
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", raw_output_path,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        final_output_path
    ]
    # Thực thi lệnh FFmpeg trong hệ điều hành và ẩn toàn bộ log đầu ra
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Xóa file video thô sau khi đã chuyển mã nén thành công sang file H.264
    remove_file(raw_output_path)

    # Nếu người dùng không chọn lưu trữ file lâu dài
    if not save:
        # Đăng ký tác vụ nền tự động xóa file thành phẩm sau khi hoàn tất truyền cho client
        background_tasks.add_task(remove_file, final_output_path)

    # Tính toán tổng thời gian xử lý video theo đơn vị giây
    process_time = time.perf_counter() - start_time
    # Đóng gói thời gian xử lý vào custom header
    headers = {"X-Process-Time": f"{process_time:.2f}s"}

    # Trả về phản hồi dạng FileResponse kèm background task dọn dẹp nếu không lưu
    return FileResponse(
        final_output_path,
        media_type="video/mp4",
        filename=final_output_filename,
        headers=headers,
        background=background_tasks if not save else None
    )
