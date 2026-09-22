// Nhập các React hook quản lý trạng thái và vòng đời component
import { useState, useEffect } from 'react';

// Xuất component chính của ứng dụng
export default function App() {
  // Quản lý file nhị phân được người dùng chọn tải lên
  const [file, setFile] = useState(null);
  // Quản lý kiểu file đang xử lý: "image" hoặc "video"
  const [fileType, setFileType] = useState("image");
  // Quản lý giá trị ngưỡng tự tin nhận diện (từ 0.05 đến 0.95)
  const [confidence, setConfidence] = useState(0.25);
  // Quản lý trạng thái checkbox lưu trữ file trên máy chủ
  const [saveResult, setSaveResult] = useState(false);
  // Quản lý URL xem trước của file đầu vào
  const [previewUrl, setPreviewUrl] = useState(null);
  // Quản lý URL kết quả nhận diện trả về từ server
  const [resultUrl, setResultUrl] = useState(null);
  // Quản lý chuỗi thời gian xử lý nhận diện đọc từ header
  const [processTime, setProcessTime] = useState(null);
  // Quản lý trạng thái đang gửi request xử lý dữ liệu
  const [loading, setLoading] = useState(false);
  // Quản lý chuỗi thông báo lỗi khi có sự cố
  const [error, setError] = useState(null);
  // Quản lý mảng danh sách lịch sử các file đã lưu từ server
  const [history, setHistory] = useState([]);

  // Hàm bất đồng bộ gọi API lấy danh sách file đã lưu
  const fetchHistory = async () => {
    try {
      // Gửi yêu cầu GET qua đường dẫn tương đối để Nginx chuyển tiếp sang Backend
      const res = await fetch("/api/results");
      // Nếu server phản hồi trạng thái thành công HTTP 200
      if (res.ok) {
        // Giải mã gói dữ liệu JSON
        const data = await res.json();
        // Cập nhật dữ liệu vào biến state history
        setHistory(data);
      }
    } catch (e) {
      // In lỗi ra console nếu không gọi được API
      console.error("Không thể tải lịch sử:", e);
    }
  };

  // Hook thực thi một lần duy nhất ngay sau khi component hiển thị lần đầu
  useEffect(() => {
    // Tự động tải danh sách lịch sử file khi mở ứng dụng
    fetchHistory();
  }, []);

  // Hàm xử lý sự kiện khi người dùng chọn file từ máy tính
  const handleFileChange = (e) => {
    // Lấy file đầu tiên từ danh sách file đã chọn
    const selected = e.target.files[0];
    // Thoát nếu người dùng hủy chọn file
    if (!selected) return;

    // Lưu file vào state
    setFile(selected);
    // Xóa sạch thông báo lỗi cũ
    setError(null);
    // Đặt lại kết quả hiển thị cũ về null
    setResultUrl(null);

    // Kiểm tra xem file được chọn có phải là video hay không
    const isVid = selected.type.includes("video");
    // Thiết lập kiểu file tương ứng
    setFileType(isVid ? "video" : "image");
    // Tạo URL blob tạm từ file cục bộ để hiển thị xem trước
    setPreviewUrl(URL.createObjectURL(selected));
  };

  // Hàm xử lý gửi yêu cầu nhận diện sang Backend
  const handleDetect = async () => {
    // Kiểm tra nếu chưa chọn file thì cảnh báo và dừng lại
    if (!file) {
      setError("Vui lòng chọn file trước!");
      return;
    }

    // Bật trạng thái loading hiển thị tiến trình
    setLoading(true);
    // Đặt lại trạng thái lỗi về rỗng
    setError(null);
    // Đặt lại hiển thị thời gian xử lý
    setProcessTime(null);

    // Khởi tạo đối tượng FormData để gửi dữ liệu dạng multipart/form-data
    const formData = new FormData();
    // Đính kèm file cần nhận diện
    formData.append("file", file);
    // Đính kèm giá trị confidence dưới dạng chuỗi
    formData.append("confidence", String(confidence));
    // Đính kèm cờ lưu trữ kết quả dưới dạng chuỗi
    formData.append("save", String(saveResult));

    // Xác định endpoint tương đối tùy theo loại file đang xử lý
    const endpoint = fileType === "video" 
      ? "/api/detect/video" 
      : "/api/detect/image";

    try {
      // Thực hiện gửi POST request thông qua Nginx Reverse Proxy
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      // Nếu server trả về mã lỗi HTTP không thành công
      if (!response.ok) {
        // Ném ra ngoại lệ kèm mã lỗi
        throw new Error(`Server báo lỗi: ${response.status} ${response.statusText}`);
      }
      
      // Đọc giá trị thời gian xử lý từ header phản hồi
      const timeHeader = response.headers.get("X-Process-Time");
      // Cập nhật giá trị vào state nếu header này tồn tại
      if (timeHeader) setProcessTime(timeHeader);

      // Đọc toàn bộ luồng byte kết quả thành một đối tượng Blob
      const blobData = await response.blob();
      // Tạo URL truy cập tạm thời cho đối tượng Blob vừa nhận
      const outputUrl = URL.createObjectURL(blobData);
      // Gán URL này vào state để hiển thị kết quả ra màn hình
      setResultUrl(outputUrl);

      // Nếu có bật tùy chọn lưu file
      if (saveResult) {
        // Đợi 1 giây rồi cập nhật lại danh sách lịch sử hiển thị
        setTimeout(fetchHistory, 1000);
      }
    } catch (err) {
      // Ghi nhận lỗi và hiển thị thông báo ra giao diện
      setError(err.message || "Không thể kết nối đến Backend!");
    } finally {
      // Tắt trạng thái loading khi quá trình kết thúc
      setLoading(false);
    }
  };

  // Trả về cấu trúc cây DOM JSX để render giao diện
  return (
    // Khung chứa giao diện toàn trang
    <div style={{ maxWidth: "950px", margin: "30px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      {/* Tiêu đề ứng dụng */}
      <h2>Bảng Điều Khiển Nhận Diện YOLO (W2 & W3)</h2>

      {/* Cụm điều khiển thông số và nạp file */}
      <div style={{ padding: "18px", border: "1px solid #ddd", borderRadius: "8px", background: "#fafafa" }}>
        {/* Hàng chứa các công cụ điều khiển */}
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "15px" }}>
          {/* Nút chọn file từ máy tính */}
          <input 
            type="file" 
            accept="image/jpeg,image/png,video/mp4" 
            onChange={handleFileChange} 
            disabled={loading}
          />

          {/* Cụm điều chỉnh thanh trượt Confidence */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {/* Nhãn hiển thị giá trị độ tin cậy hiện tại */}
            <label htmlFor="confRange" style={{ fontSize: "14px", fontWeight: "bold" }}>
              Confidence: <span style={{ color: "#0066cc" }}>{confidence}</span>
            </label>
            {/* Thanh trượt điều chỉnh ngưỡng nhận diện */}
            <input 
              id="confRange"
              type="range" 
              min="0.05" 
              max="0.95" 
              step="0.05" 
              value={confidence} 
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              disabled={loading}
              style={{ cursor: "pointer" }}
            />
          </div>

          {/* Cụm checkbox chọn lưu kết quả trên server */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            {/* Checkbox lưu trữ */}
            <input 
              type="checkbox" 
              id="saveCheck" 
              checked={saveResult} 
              onChange={(e) => setSaveResult(e.target.checked)}
              disabled={loading} 
            />
            {/* Nhãn của checkbox */}
            <label htmlFor="saveCheck" style={{ fontSize: "14px", cursor: "pointer", fontWeight: "500" }}>
              Lưu kết quả trên máy chủ
            </label>
          </div>

          {/* Nút kích hoạt tiến trình nhận diện */}
          <button 
            onClick={handleDetect} 
            disabled={loading || !file}
            style={{ 
              padding: "8px 20px", 
              backgroundColor: (loading || !file) ? "#ccc" : "#007bff",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: (loading || !file) ? "not-allowed" : "pointer"
            }}
          >
            {/* Thay đổi nhãn nút dựa trên trạng thái loading */}
            {loading ? "Đang xử lý..." : "Chạy Nhận Diện"}
          </button>
        </div>
      </div>

      {/* Hiển thị khung thông báo lỗi nếu có */}
      {error && (
        <p style={{ color: "red", padding: "10px", background: "#ffebee", borderRadius: "4px", marginTop: "15px" }}>
          <strong>Lỗi:</strong> {error}
        </p>
      )}

      {/* Vùng bố cục lưới 2 cột hiển thị so sánh đầu vào và đầu ra */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginTop: "25px" }}>
        {/* Cột 1: Hiển thị file đầu vào */}
        <div>
          <h4>1. Dữ liệu đầu vào:</h4>
          {/* Kiểm tra đã có file preview chưa */}
          {previewUrl ? (
            // Nếu là video thì render thẻ video
            fileType === "video" ? (
              <video src={previewUrl} controls style={{ width: "100%", borderRadius: "6px" }} />
            ) : (
              // Nếu là ảnh thì render thẻ img
              <img src={previewUrl} alt="Input" style={{ width: "100%", borderRadius: "6px" }} />
            )
          ) : (
            // Thông báo khi chưa chọn file
            <p style={{ color: "#888" }}>Chưa nạp file.</p>
          )}
        </div>

        {/* Cột 2: Hiển thị kết quả từ Backend */}
        <div>
          <h4>2. Kết quả từ Backend:</h4>
          {/* Hiển thị thời gian inference nếu có */}
          {processTime && (
            <p style={{ color: "#28a745", fontWeight: "bold", margin: "5px 0 12px 0" }}>
              ⏱️ Thời gian xử lý: {processTime}
            </p>
          )}
          {/* Thông báo tiến trình đang chạy */}
          {loading && <p style={{ color: "#0066cc" }}>Mô hình đang inference dữ liệu...</p>}

          {/* Hiển thị thành phẩm sau khi nhận diện xong */}
          {!loading && resultUrl && (
            // Nếu là video thì render thẻ video có autoPlay
            fileType === "video" ? (
              <video src={resultUrl} controls autoPlay style={{ width: "100%", borderRadius: "6px" }} />
            ) : (
              // Nếu là ảnh thì render thẻ img
              <img src={resultUrl} alt="YOLO Output" style={{ width: "100%", borderRadius: "6px" }} />
            )
          )}

          {/* Thông báo khi chưa có kết quả */}
          {!loading && !resultUrl && <p style={{ color: "#888" }}>Chưa có kết quả.</p>}
        </div>
      </div>

      {/* Vùng hiển thị danh sách các kết quả đã lưu lại */}
      <div style={{ marginTop: "40px", borderTop: "2px dashed #eee", paddingTop: "20px" }}>
        {/* Tiêu đề danh mục lịch sử kèm số lượng phần tử */}
        <h3>📁 Kết quả đã lưu trên hệ thống ({history.length})</h3>
        {/* Kiểm tra danh sách có rỗng không */}
        {history.length === 0 ? (
          // Thông báo hướng dẫn khi chưa có file lưu
          <p style={{ color: "#888" }}>Chưa có file nào được lưu. Tích chọn "Lưu kết quả trên máy chủ" khi chạy để lưu lại.</p>
        ) : (
          // Lưới bố cục hiển thị danh sách các thẻ kết quả
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "15px" }}>
            {/* Lặp qua từng phần tử trong mảng history */}
            {history.map((item, idx) => (
              // Khung card cho từng file kết quả
              <div key={idx} style={{ border: "1px solid #ddd", borderRadius: "6px", padding: "8px", background: "#fff" }}>
                {/* Kiểm tra kiểu file để render thẻ media tương ứng */}
                {item.type === "video" ? (
                  // Thẻ video kết quả (gọi qua proxy /static/...)
                  <video src={item.url} controls style={{ width: "100%", height: "120px", objectFit: "cover" }} />
                ) : (
                  // Thẻ ảnh kết quả (gọi qua proxy /static/...)
                  <img src={item.url} alt="Saved item" style={{ width: "100%", height: "120px", objectFit: "cover" }} />
                )}
                {/* Tên file kết quả */}
                <p style={{ fontSize: "12px", margin: "6px 0 2px 0", wordBreak: "break-all" }}>{item.filename}</p>
                {/* Thời gian tạo file */}
                <span style={{ fontSize: "11px", color: "#666" }}>{item.created_at}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
