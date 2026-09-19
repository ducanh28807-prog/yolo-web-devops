import io
import cv2
import numpy as np
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# 1. Test endpoint kiểm tra sức khỏe hệ thống
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# 2. Test upload ảnh đúng định dạng (Tạo ảnh giả lập bằng OpenCV trong bộ nhớ)
def test_detect_image_success():
    # Tạo một ảnh dummy 100x100 màu đen
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode(".jpg", img)
    image_bytes = io.BytesIO(img_encoded.tobytes())

    response = client.post(
        "/api/detect/image",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")},
        data={"confidence": 0.25}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


# 3. Test upload sai loại file (Gửi file .txt để kiểm tra mã lỗi 415)
def test_detect_image_invalid_file_type():
    fake_txt_file = io.BytesIO(b"This is a plain text file, not an image.")

    response = client.post(
        "/api/detect/image",
        files={"file": ("test.txt", fake_txt_file, "text/plain")},
        data={"confidence": 0.25}
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Chỉ chấp nhận file ảnh JPG hoặc PNG."
