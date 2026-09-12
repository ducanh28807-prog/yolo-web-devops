import { useState } from 'react';

export default function App() {
  // 1. VÙNG NHỚ TRẠNG THÁI (RAM)
  const [file, setFile] = useState(null);               // File thô người dùng chọn
  const [fileType, setFileType] = useState("image");    // Cờ: "image" hoặc "video"[cite: 1]
  const [confidence, setConfidence] = useState(0.25);   // Ngưỡng tin cậy (Confidence threshold)
  const [previewUrl, setPreviewUrl] = useState(null);   // Link xem trước ảnh/video gốc[cite: 1]
  const [resultUrl, setResultUrl] = useState(null);     // Link xem kết quả YOLO (tạo từ Blob)[cite: 1]
  const [processTime, setProcessTime] = useState(null); // <--- [THÊM DÒNG NÀY]
  const [loading, setLoading] = useState(false);        // Cờ ngắt khóa nút bấm[cite: 1]
  const [error, setError] = useState(null);             // Thông báo lỗi nếu server sập[cite: 1]

  // 2. KHI NGƯỜI DÙNG CHỌN FILE
  const handleFileChange = (e) => {
    const selected = e.target.files[0]; //[cite: 1]
    if (!selected) return; //[cite: 1]

    setFile(selected); //[cite: 1]
    setError(null); //[cite: 1]
    setResultUrl(null); //[cite: 1]

    const isVid = selected.type.includes("video"); //[cite: 1]
    setFileType(isVid ? "video" : "image"); //[cite: 1]

    setPreviewUrl(URL.createObjectURL(selected)); //[cite: 1]
  };

  // 3. GỬI DỮ LIỆU SANG FASTAPI
  const handleDetect = async () => {
    if (!file) { //[cite: 1]
      setError("Vui lòng chọn file trước!"); //[cite: 1]
      return; //[cite: 1]
    }

    setLoading(true); //[cite: 1]
    setError(null); //[cite: 1]
    setProcessTime(null); // <--- [THÊM DÒNG NÀY]: Xóa kết quả thời gian của lần chạy cũ

    // Đóng gói file và ngưỡng confidence động
    const formData = new FormData(); //[cite: 1]
    formData.append("file", file); //[cite: 1]
    formData.append("confidence", String(confidence)); // Gửi giá trị từ thanh trượt

    const endpoint = fileType === "video" 
      ? "http://localhost:8000/api/detect/video" 
      : "http://localhost:8000/api/detect/image"; //[cite: 1]

    try {
      const response = await fetch(endpoint, {
        method: "POST", //[cite: 1]
        body: formData, //[cite: 1]
      });

      if (!response.ok) { //[cite: 1]
        throw new Error(`Server báo lỗi: ${response.status} ${response.statusText}`); //[cite: 1]
      }
      
      // <--- [THÊM 2 DÒNG NÀY]: Bóc dữ liệu X-Process-Time từ Backend trả về
      const timeHeader = response.headers.get("X-Process-Time");
      if (timeHeader) setProcessTime(timeHeader);

      const blobData = await response.blob(); //[cite: 1]
      const outputUrl = URL.createObjectURL(blobData); //[cite: 1]
      setResultUrl(outputUrl); //[cite: 1]
    } catch (err) {
      setError(err.message || "Không thể kết nối đến Backend!"); //[cite: 1]
    } finally {
      setLoading(false); //[cite: 1]
    }
  };

  return (
    <div style={{ maxWidth: "900px", margin: "30px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      <h2>Bảng Điều Khiển Nhận Diện YOLO (W3)</h2>

      {/* CỤM ĐIỀU KHIỂN */}
      <div style={{ padding: "18px", border: "1px solid #ddd", borderRadius: "8px", background: "#fafafa" }}>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "15px" }}>
          {/* Ô chọn file */}
          <input 
            type="file" 
            accept="image/jpeg,image/png,video/mp4" 
            onChange={handleFileChange} 
            disabled={loading} //[cite: 1]
          />

          {/* Thanh trượt Confidence */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <label htmlFor="confRange" style={{ fontSize: "14px", fontWeight: "bold" }}>
              Confidence: <span style={{ color: "#0066cc" }}>{confidence}</span>
            </label>
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

          {/* Nút bấm chạy */}
          <button 
            onClick={handleDetect} 
            disabled={loading || !file} //[cite: 1]
            style={{ 
              padding: "8px 20px", 
              backgroundColor: (loading || !file) ? "#ccc" : "#007bff", //[cite: 1]
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: (loading || !file) ? "not-allowed" : "pointer" //[cite: 1]
            }}
          >
            {loading ? "Đang xử lý..." : "Chạy Nhận Diện"}
          </button>
        </div>
      </div>

      {/* THÔNG BÁO LỖI */}
      {error && (
        <p style={{ color: "red", padding: "10px", background: "#ffebee", borderRadius: "4px", marginTop: "15px" }}>
          <strong>Lỗi:</strong> {error}
        </p>
      )}

      {/* VÙNG SO SÁNH TRỰC QUAN HAI BÊN */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginTop: "25px" }}>
        {/* CỘT TRÁI: DỮ LIỆU GỐC */}
        <div>
          <h4>1. Dữ liệu đầu vào:</h4>
          {previewUrl ? (
            fileType === "video" ? (
              <video src={previewUrl} controls style={{ width: "100%", borderRadius: "6px" }} /> //[cite: 1]
            ) : (
              <img src={previewUrl} alt="Input" style={{ width: "100%", borderRadius: "6px" }} /> //[cite: 1]
            )
          ) : (
            <p style={{ color: "#888" }}>Chưa nạp file.</p> //[cite: 1]
          )}
        </div>

        {/* CỘT PHẢI: KẾT QUẢ TỪ YOLO */}
        <div>
          <h4>2. Kết quả từ Backend:</h4>
          
          {processTime && (
            <p style={{ color: "#28a745", fontWeight: "bold", margin: "5px 0 12px 0" }}>
              ⏱️ Thời gian xử lý: {processTime}
            </p>
          )}
          
          {loading && <p style={{ color: "#0066cc" }}>Mô hình đang inference dữ liệu...</p>}

          {!loading && resultUrl && (
            fileType === "video" ? (
              <video src={resultUrl} controls autoPlay style={{ width: "100%", borderRadius: "6px" }} /> //[cite: 1]
            ) : (
              <img src={resultUrl} alt="YOLO Output" style={{ width: "100%", borderRadius: "6px" }} /> //[cite: 1]
            )
          )}

          {!loading && !resultUrl && (
            <p style={{ color: "#888" }}>Chưa có kết quả.</p> //[cite: 1]
          )}
        </div>
      </div>
    </div>
  );
}
