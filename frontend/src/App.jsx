import { useState, useEffect } from 'react';

export default function App() {
  const [file, setFile] = useState(null);
  const [fileType, setFileType] = useState("image");
  const [confidence, setConfidence] = useState(0.25);
  const [saveResult, setSaveResult] = useState(false); // <--- [MỚI]: Cờ kiểm soát lưu file
  const [previewUrl, setPreviewUrl] = useState(null);
  const [resultUrl, setResultUrl] = useState(null);
  const [processTime, setProcessTime] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);          // <--- [MỚI]: Lưu danh sách lịch sử

  // [MỚI]: Tải danh sách kết quả đã lưu từ Server
  const fetchHistory = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/results");
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error("Không thể tải lịch sử:", e);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (!selected) return;

    setFile(selected);
    setError(null);
    setResultUrl(null);

    const isVid = selected.type.includes("video");
    setFileType(isVid ? "video" : "image");
    setPreviewUrl(URL.createObjectURL(selected));
  };

  const handleDetect = async () => {
    if (!file) {
      setError("Vui lòng chọn file trước!");
      return;
    }

    setLoading(true);
    setError(null);
    setProcessTime(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("confidence", String(confidence));
    formData.append("save", String(saveResult)); // <--- [MỚI]: Gửi cờ save sang Backend

    const endpoint = fileType === "video" 
      ? "http://localhost:8000/api/detect/video" 
      : "http://localhost:8000/api/detect/image";

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server báo lỗi: ${response.status} ${response.statusText}`);
      }
      
      const timeHeader = response.headers.get("X-Process-Time");
      if (timeHeader) setProcessTime(timeHeader);

      const blobData = await response.blob();
      const outputUrl = URL.createObjectURL(blobData);
      setResultUrl(outputUrl);

      // Nếu có yêu cầu lưu, cập nhật lại danh sách lịch sử hiển thị
      if (saveResult) {
        setTimeout(fetchHistory, 1000);
      }
    } catch (err) {
      setError(err.message || "Không thể kết nối đến Backend!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "950px", margin: "30px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      <h2>Bảng Điều Khiển Nhận Diện YOLO (W2 & W3)</h2>

      {/* CỤM ĐIỀU KHIỂN */}
      <div style={{ padding: "18px", border: "1px solid #ddd", borderRadius: "8px", background: "#fafafa" }}>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "15px" }}>
          <input 
            type="file" 
            accept="image/jpeg,image/png,video/mp4" 
            onChange={handleFileChange} 
            disabled={loading}
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

          {/* [MỚI]: Checkbox Lưu trữ */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <input 
              type="checkbox" 
              id="saveCheck" 
              checked={saveResult} 
              onChange={(e) => setSaveResult(e.target.checked)}
              disabled={loading} 
            />
            <label htmlFor="saveCheck" style={{ fontSize: "14px", cursor: "pointer", fontWeight: "500" }}>
              Lưu kết quả trên máy chủ
            </label>
          </div>

          {/* Nút bấm chạy */}
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
            {loading ? "Đang xử lý..." : "Chạy Nhận Diện"}
          </button>
        </div>
      </div>

      {error && (
        <p style={{ color: "red", padding: "10px", background: "#ffebee", borderRadius: "4px", marginTop: "15px" }}>
          <strong>Lỗi:</strong> {error}
        </p>
      )}

      {/* VÙNG SO SÁNH TRỰC QUAN */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginTop: "25px" }}>
        <div>
          <h4>1. Dữ liệu đầu vào:</h4>
          {previewUrl ? (
            fileType === "video" ? (
              <video src={previewUrl} controls style={{ width: "100%", borderRadius: "6px" }} />
            ) : (
              <img src={previewUrl} alt="Input" style={{ width: "100%", borderRadius: "6px" }} />
            )
          ) : (
            <p style={{ color: "#888" }}>Chưa nạp file.</p>
          )}
        </div>

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
              <video src={resultUrl} controls autoPlay style={{ width: "100%", borderRadius: "6px" }} />
            ) : (
              <img src={resultUrl} alt="YOLO Output" style={{ width: "100%", borderRadius: "6px" }} />
            )
          )}

          {!loading && !resultUrl && <p style={{ color: "#888" }}>Chưa có kết quả.</p>}
        </div>
      </div>

      {/* [MỚI]: BẢNG LỊCH SỬ KẾT QUẢ ĐÃ LƯU */}
      <div style={{ marginTop: "40px", borderTop: "2px dashed #eee", paddingTop: "20px" }}>
        <h3>📁 Kết quả đã lưu trên hệ thống ({history.length})</h3>
        {history.length === 0 ? (
          <p style={{ color: "#888" }}>Chưa có file nào được lưu. Tích chọn "Lưu kết quả trên máy chủ" khi chạy để lưu lại.</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "15px" }}>
            {history.map((item, idx) => (
              <div key={idx} style={{ border: "1px solid #ddd", borderRadius: "6px", padding: "8px", background: "#fff" }}>
                {item.type === "video" ? (
                  <video src={item.url} controls style={{ width: "100%", height: "120px", objectFit: "cover" }} />
                ) : (
                  <img src={item.url} alt="Saved item" style={{ width: "100%", height: "120px", objectFit: "cover" }} />
                )}
                <p style={{ fontSize: "12px", margin: "6px 0 2px 0", wordBreak: "break-all" }}>{item.filename}</p>
                <span style={{ fontSize: "11px", color: "#666" }}>{item.created_at}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
