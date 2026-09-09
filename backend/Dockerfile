# 1. Base image Python slim
FROM python:3.10-slim

# 2. Cài đặt các thư viện hệ thống cần thiết cho OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Ép cài đặt PyTorch bản CPU-only trước (chỉ khoảng 200MB thay vì 5GB)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 4. Sau đó mới cài các thư viện còn lại (FastAPI, OpenCV, Ultralytics)
# Lúc này Ultralytics thấy đã có sẵn Torch CPU rồi nên sẽ không kéo CUDA về nữa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy mã nguồn
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
