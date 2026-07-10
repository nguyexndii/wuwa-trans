# Wuthering Waves Screen Translator 🎮🗣️

Một ứng dụng dịch thuật hội thoại màn hình nhẹ nhàng, chạy trực tiếp trên Terminal Windows. Ứng dụng chụp màn hình, sử dụng API Gemini để tự động phát hiện, dịch thuật ngữ cảnh hội thoại, tự động học xưng hô và hiển thị đè bản dịch bằng lớp phủ (Overlay) trong suốt hỗ trợ Click-Through.

---

## 🌟 Tính Năng Nổi Bật

1. **Dịch Thuật Thông Minh Bằng Gemini 2.5 Flash:**
   - Dịch thuật kết hợp **Thị giác máy tính (Multimodal Vision)** và **Suy luận nháp (Chain of Thought / Self-Refinement)** để tạo ra bản dịch trơn tru, tự nhiên nhất.
   - Dịch có ngữ cảnh: Mặc định tối ưu hóa cho nhân vật chính là **Rover Nữ** (hoặc Rover Nam tùy chọn). AI tự động chọn đại từ nhân xưng thích hợp ("cô", "em", "nàng", "chị", "ta", "ngươi"...) phù hợp với từng nhân vật.

2. **Bộ Nhớ Nhân Vật Tự Học (`character_memory.json`):**
   - Tự động nhận diện giới tính và thái độ/quan hệ của các NPC mới xuất hiện đối với bạn.
   - Lưu trữ, nâng cấp tần suất xuất hiện và xếp hạng bằng công thức:
     $$\text{Score} = \text{use\_count} + \frac{10}{\text{seconds\_since\_last\_used} + 1.0}$$
   - Lọc và gửi tối đa **Top 10** nhân vật hoạt động nhiều/gần đây nhất để tránh làm loãng ngữ cảnh AI.

3. **Từ Điển Thuật Ngữ Học Tập (`glossary.json`):**
   - Tự động dịch thuật ngữ cốt truyện, tên quái, kỹ năng theo phong cách Hán-Việt kết hợp chú thích tiếng Anh trong ngoặc đơn, ví dụ: *Kim Châu (Jinzhou)*, *Dị Vật Tacet (Tacet Discord)*, *Dư Âm (Echo)*.
   - Lọc và gửi tối đa **Top 40** thuật ngữ có độ ưu tiên cao nhất theo công thức tương tự.

4. **Lớp Phủ Phụ Đề Thông Minh (Overlay & Click-Through):**
   - Hiển thị phụ đề cố định nằm ngang đẹp mắt ở cạnh dưới màn hình game khi nhấn phím tắt **`Alt + Q`** (Auto Mode).
   - Cho phép vẽ vùng chọn thủ công bằng cách gõ **`?`** vào Terminal để dịch các bảng mô tả kỹ năng, vật phẩm.
   - **Click-Through:** Chuột có thể click xuyên qua chữ dịch để tiếp tục bấm game thoải mái.
   - **Hover to Hide:** Khi di chuột vào vùng chữ dịch, chữ sẽ tự động mờ đi 10% để bạn đọc chữ tiếng Anh gốc bên dưới, đồng thời đóng băng thời gian tự tắt (8s) để bạn kịp đọc hết.

5. **Độ Bền & Độ Chịu Lỗi Cao:**
   - **Xoay Vòng API Key:** Tự động đổi API Key khác khi key hiện tại bị lỗi/hết hạn ngạch.
   - **Exponential Backoff Retry:** Nếu toàn bộ key đều bị lỗi (như rate-limit tạm thời), tự động chờ và thử lại tối đa 3 lần với khoảng cách chờ tăng dần (`2s, 4s, 6s...`).
   - **Ghi File An Toàn (Atomic Writing):** Dữ liệu cấu hình và bộ nhớ được ghi ra file tạm `.tmp` trước khi đổi tên đè lên file chính, chống hỏng file JSON khi app bị tắt đột ngột.
   - **Xoay Vòng File Log:** Giới hạn dung lượng `game_dialogue_log.txt` tối đa 1MB (tự đổi tên thành `.txt.bak` khi đầy), không gây tốn ổ đĩa.

---

## 🛠️ Cài Đặt và Khởi Chạy

### 1. Chuẩn Bị Môi Trường
- Tải và cài đặt [Python](https://www.python.org/) bản mới nhất (nhớ tích chọn **Add Python to PATH**).

### 2. Thiết Lập Ứng Dụng
1. Tải toàn bộ mã nguồn về máy và đưa vào thư mục mong muốn (ví dụ: `d:\wuwa-trans`).
2. Mở Command Prompt (CMD) hoặc PowerShell **dưới quyền Administrator** (bắt buộc để lắng nghe phím tắt Alt+Q khi đang ở trong game).
3. Di chuyển đến thư mục dự án và khởi chạy file cài đặt môi trường và phím tắt:
   ```cmd
   py setup.py
   ```
4. Quá trình thiết lập sẽ:
   - Tạo môi trường ảo `.venv` và cài đặt các thư viện cần thiết.
   - Tạo file chạy nhanh `Run_Translator.bat`.
   - Tạo shortcut `Wuthering Waves Translator` ngoài Desktop và trong thư mục dự án.

### 3. Ghim ứng dụng lên Taskbar (Thanh tác vụ)
- Click chuột phải vào shortcut **Wuthering Waves Translator** ngoài Desktop hoặc thư mục và chọn **Pin to taskbar** (Ghim vào thanh tác vụ).

---

## 🚀 Hướng Dẫn Sử Dụng

1. **Khởi Chạy:** Click chuột phải vào biểu tượng ứng dụng ở Taskbar hoặc file `.bat` và chọn **Run as administrator** (Chạy dưới quyền quản trị viên).
2. **Nhập API Key lần đầu:** Điền danh sách Gemini API Key của bạn (lấy miễn phí tại [Google AI Studio](https://aistudio.google.com/)). Bạn có thể nhập nhiều key phân cách nhau bằng dấu phẩy `,`.
3. **Sử dụng trong game:**
   - **`Alt + Q`**: Chụp màn hình và tự dịch hội thoại chính của game hiện lên thanh phụ đề dưới màn hình.
   - **Nhập `?` vào Terminal:** Vẽ vùng chọn thủ công bằng chuột để dịch đoạn văn bản bất kỳ.
   - **Nhập `clear` vào Terminal:** Xóa lịch sử ngữ cảnh hội thoại hiện tại.
   - **Nhập `exit` hoặc `q` vào Terminal:** Thoát ứng dụng.

---

## ⚙️ Cấu Hình Cá Nhân (`config.json`)

Bạn có thể chỉnh sửa các thông số sau trong `config.json`:
- `gemini_api_keys`: Mảng danh sách API keys để xoay vòng.
- `model_name`: Model sử dụng (mặc định là `gemini-2.5-flash`).
- `rover_gender`: Giới tính nhân vật chính (`female` cho Rover Nữ, `male` cho Rover Nam).
- `overlay_duration_seconds`: Thời gian hiển thị phụ đề trước khi tự biến mất (mặc định là `8` giây).
- `use_fixed_subtitle`: Bật (`true`)/Tắt (`false`) chế độ hiển thị phụ đề cố định cạnh dưới màn hình.
