# ==========================================
# GIAI ĐOẠN 1: BUILD MÃ NGUỒN (BUILD STAGE)
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Tận dụng cơ chế Layer Caching của Docker
COPY package.json package-lock.json ./

# Cài đặt chính xác các thư viện theo lockfile
RUN npm ci

# Sao chép toàn bộ mã nguồn còn lại vào container
COPY . .

# Biên dịch code React/JSX thành các file tĩnh (HTML, JS, CSS) trong thư mục dist/
RUN npm run build


# ==========================================
# GIAI ĐOẠN 2: CHẠY WEB SERVER (PRODUCTION STAGE)
# ==========================================
FROM nginx:alpine

# Xóa các file mặc định của Nginx
RUN rm -rf /usr/share/nginx/html/*

# Sao chép thành phẩm đã build từ Giai đoạn 1 sang thư mục web của Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Khai báo container lắng nghe tại cổng 80
EXPOSE 80

# Chạy Nginx ở chế độ foreground để giữ container luôn sống
CMD ["nginx", "-g", "daemon off;"]
