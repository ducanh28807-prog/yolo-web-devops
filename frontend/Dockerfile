# STAGE 1: Môi trường Node.js đóng gói mã nguồn React
FROM node:20-alpine AS builder

# Khởi tạo thư mục làm việc bên trong container cho Stage 1
WORKDIR /app

# Sao chép các file quản lý gói thư viện vào container trước để tận dụng cache
COPY package.json package-lock.json ./

# Cài đặt toàn bộ dependencies theo đúng khóa trong file lock
RUN npm ci

# Sao chép toàn bộ mã nguồn frontend vào bên trong container
COPY . .

# Thực thi lệnh đóng gói React/Vite thành các file tĩnh HTML/CSS/JS trong thư mục dist/
RUN npm run build


# STAGE 2: Môi trường Nginx siêu nhẹ chạy ứng dụng và Reverse Proxy
FROM nginx:alpine

# Xóa bỏ các file giao diện mặc định ban đầu của Nginx
RUN rm -rf /usr/share/nginx/html/*

# Sao chép các file tĩnh đã build từ Stage 1 sang thư mục web của Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Sao chép file cấu hình Reverse Proxy tự viết vào đè lên file cấu hình mặc định
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Khai báo cổng 80 phục vụ kết nối HTTP
EXPOSE 80

# Chạy Nginx ở chế độ foreground để giữ container luôn hoạt động
CMD ["nginx", "-g", "daemon off;"]
