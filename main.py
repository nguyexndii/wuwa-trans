import os
import sys
import json
import time
import queue
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import mss
import keyboard
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# Define the Pydantic schema for Gemini structured output
class TranslationResult(BaseModel):
    speaker: Optional[str] = Field(default="", description="Name of the character speaking in English, or empty string if no speaker is named.")
    original_text: str = Field(default="", description="The original English text detected in the dialogue box.")
    translated_text: str = Field(default="", description="The Vietnamese translation of the dialogue text, formatted naturally according to the context.")
    box_2d: List[int] = Field(default=[0, 0, 0, 0], description="Bounding box of the dialogue/text box containing 4 integers [ymin, xmin, ymax, xmax] on a 0-1000 scale.")
    inferred_speaker_gender: Optional[str] = Field(default="unknown", description="The inferred gender of the speaker based on their appearance, name, or dialogue. Allowed values: 'male', 'female', 'unknown'.")
    inferred_relationship: Optional[str] = Field(default="neutral", description="The inferred relationship or attitude of the speaker towards Rover based on the context. Allowed values: 'friendly', 'respectful', 'hostile', 'neutral'.")
    new_terms: Optional[Dict[str, str]] = Field(default={}, description="Any game-specific terms, locations, or items detected in this dialogue, mapped as {English_term: Vietnamese_translation_with_parentheses}. Example: {'Jinzhou': 'Kim Châu (Jinzhou)'}")

class ScreenTranslatorApp:
    def __init__(self):
        self.config = self.load_config()
        self.api_keys = self.get_api_keys()
        self.current_key_idx = 0
        self.history = []
        self.current_overlay = None
        self.translating_indicator = None
        self.gui_queue = queue.Queue()
            
        # Log file
        self.log_file = "game_dialogue_log.txt"
        
        # Character Memory
        self.character_memory_file = "character_memory.json"
        self.character_memory = self.load_character_memory()
        
        # Glossary (Terminology Memory)
        self.glossary_file = "glossary.json"
        self.glossary = self.load_glossary()

    def load_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        default_config = {
            "gemini_api_keys": [],
            "model_name": "gemini-2.5-flash",
            "rover_gender": "female",
            "history_limit": 10,
            "overlay_duration_seconds": 8
        }
        self.save_config(default_config)
        return default_config

    def save_config(self, config):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def load_character_memory(self):
        if os.path.exists(self.character_memory_file):
            try:
                with open(self.character_memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_character_memory(self):
        try:
            with open(self.character_memory_file, "w", encoding="utf-8") as f:
                json.dump(self.character_memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Lỗi lưu bộ nhớ nhân vật: {e}")

    def update_character_memory(self, speaker, gender, relationship):
        if not speaker or speaker.lower() in ["unknown", "nhân vật", "lỗi", ""] or speaker.strip() == "":
            return False
            
        speaker = speaker.strip()
        gender = gender.lower() if gender else "unknown"
        relationship = relationship.lower() if relationship else "neutral"
        
        changed = False
        
        # If character is not in memory
        if speaker not in self.character_memory:
            self.character_memory[speaker] = {
                "gender": gender,
                "relationship": relationship
            }
            changed = True
            print(f"\n[Bộ nhớ nhân vật] Đã học nhân vật mới: {speaker} (Giới tính: {gender}, Quan hệ: {relationship})")
        else:
            # If character exists but has 'unknown' gender and we now have a real gender
            existing = self.character_memory[speaker]
            if existing.get("gender") == "unknown" and gender != "unknown":
                existing["gender"] = gender
                changed = True
                print(f"\n[Bộ nhớ nhân vật] Cập nhật giới tính cho {speaker}: {gender}")
            if existing.get("relationship") == "neutral" and relationship != "neutral":
                existing["relationship"] = relationship
                changed = True
                print(f"\n[Bộ nhớ nhân vật] Cập nhật quan hệ cho {speaker}: {relationship}")
                
        if changed:
            self.save_character_memory()
            return True
        return False

    def load_glossary(self):
        default_glossary = {
            "Resonator": "Người Cộng Hưởng (Resonator)",
            "Tacet Discord": "Dị Vật Tacet (Tacet Discord)",
            "Jinzhou": "Kim Châu (Jinzhou)",
            "Huanglong": "Hoàng Long (Huanglong)",
            "Forte": "Kỹ Năng Forte (Forte)",
            "Echo": "Dư Âm (Echo)"
        }
        if os.path.exists(self.glossary_file):
            try:
                with open(self.glossary_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge default keys if they don't exist
                    for k, v in default_glossary.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception:
                pass
        
        # Save defaults if no file exists
        try:
            with open(self.glossary_file, "w", encoding="utf-8") as f:
                json.dump(default_glossary, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return default_glossary

    def save_glossary(self):
        try:
            with open(self.glossary_file, "w", encoding="utf-8") as f:
                json.dump(self.glossary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Lỗi lưu từ điển thuật ngữ: {e}")

    def update_glossary(self, new_terms):
        if not new_terms:
            return False
        changed = False
        for eng, vi in new_terms.items():
            eng_clean = eng.strip()
            vi_clean = vi.strip()
            if eng_clean and vi_clean and eng_clean not in self.glossary:
                self.glossary[eng_clean] = vi_clean
                changed = True
                print(f"\n[Từ điển thuật ngữ] Đã học thuật ngữ mới: {eng_clean} -> {vi_clean}")
        if changed:
            self.save_glossary()
            return True
        return False

    def get_api_keys(self):
        # Check environment variable first
        env_key = os.environ.get("GEMINI_API_KEY")
        if env_key:
            return [env_key]
            
        # Check list of keys in config
        keys = self.config.get("gemini_api_keys", [])
        if not keys and self.config.get("gemini_api_key"):
            keys = [self.config["gemini_api_key"]]
            
        if not keys:
            print("="*60)
            print(" CHƯA TÌM THẤY GEMINI API KEY ")
            print(" Vui lòng truy cập https://aistudio.google.com/ để lấy API Key miễn phí.")
            print("="*60)
            key = input("Nhập Gemini API Key của bạn (nhập nhiều key ngăn cách bằng dấu phẩy): ").strip()
            if key:
                keys = [k.strip() for k in key.split(",") if k.strip()]
                self.config["gemini_api_keys"] = keys
                self.save_config(self.config)
                print(f"Đã lưu {len(keys)} API Key vào config.json!")
            else:
                print("Lỗi: Cần ít nhất 1 API Key để chạy ứng dụng.")
                sys.exit(1)
        return keys

    def log_translation(self, speaker, original, translated):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        speaker_str = speaker if speaker else "Unknown"
        log_entry = f"[{timestamp}] {speaker_str}: {original}\n -> {speaker_str}: {translated}\n"
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Lỗi ghi log file: {e}")

    def update_history(self, speaker, translated):
        self.history.append({
            "speaker": speaker if speaker else "Nhân vật",
            "text_vi": translated
        })
        limit = self.config.get("history_limit", 10)
        if len(self.history) > limit:
            self.history.pop(0)

    def capture_screen(self):
        with mss.mss() as sct:
            # Capture the primary monitor
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            # Convert to PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img, monitor["width"], monitor["height"]

    def build_prompt(self):
        history_lines = []
        for h in self.history:
            history_lines.append(f"- {h['speaker']}: {h['text_vi']}")
        
        history_str = "\n".join(history_lines) if history_lines else "Không có hội thoại trước đó."
        
        prompt = f"""
Hãy dịch hội thoại hiện tại trong bức ảnh sang tiếng Việt.

Lịch sử hội thoại gần đây để tham khảo ngữ cảnh:
{history_str}
"""
        return prompt

    def get_system_instruction(self):
        rover_gender = self.config.get("rover_gender", "female")
        gender_desc = "NỮ (Rover Nữ). Bạn và các NPC nói chuyện với Rover cần dùng các xưng hô nữ tính như 'cô', 'em', 'nàng', 'cậu', 'ta' phù hợp với quan hệ/tính cách nhân vật." if rover_gender == "female" else "NAM (Rover Nam). Dùng các xưng hô nam tính như 'anh', 'cậu', 'ta'."
        
        # Build character profiles from memory
        memory_lines = []
        for name, info in self.character_memory.items():
            memory_lines.append(f"- {name}: Giới tính {info.get('gender', 'unknown')}, mối quan hệ với Rover là {info.get('relationship', 'neutral')}")
        character_profiles = "\n".join(memory_lines) if memory_lines else "Chưa lưu thông tin nhân vật nào."
        
        # Build glossary terms
        glossary_lines = []
        for eng, vi in self.glossary.items():
            glossary_lines.append(f"- {eng}: {vi}")
        glossary_str = "\n".join(glossary_lines) if glossary_lines else "Chưa lưu thuật ngữ nào."
        
        # Quy tắc xưng hô chi tiết dựa trên Rover Nữ
        pronoun_rules = """
HƯỚNG DẪN XƯNG HÔ CHI TIẾT (Rover là NỮ):
- Nếu NPC nói là NAM và THÂN THIỆN/THÂN CẬN (friendly):
  NPC tự xưng là "anh/tôi", gọi Rover là "em/cậu" (Ví dụ: "Anh sẽ giúp em", "Cậu đi cùng tôi nhé").
- Nếu NPC nói là NỮ và THÂN THIỆN/THÂN CẬN (friendly):
  NPC tự xưng là "tớ/mình/chị", gọi Rover là "cậu/em" (Ví dụ: "Tớ đi trước nhé, cậu theo sau nha").
- Nếu NPC nói là KÍNH TRỌNG/TRỊNH TRỌNG (respectful) (Ví dụ: Tướng quân Jiyan, quan chức, bậc trưởng bối):
  NPC tự xưng là "ta/tôi", gọi Rover là "cô/Rover/cậu" (Ví dụ: "Ta khuyên cô nên cẩn thận", "Rover, cô đã đến rồi").
- Nếu NPC nói là TRUNG LẬP (neutral):
  NPC tự xưng là "tôi", gọi Rover là "cô/cậu".
- Nếu NPC nói là THÙ ĐỊCH (hostile):
  NPC tự xưng là "ta", gọi Rover là "ngươi/kẻ kia".
- Khi Rover (nhân vật chính) tự nói chuyện:
  + Nói với nhân vật nam thân thiện: tự xưng là "em/tớ", gọi họ là "anh/cậu".
  + Nói với nhân vật nữ thân thiện: tự xưng là "tớ/em", gọi họ là "cậu/chị".
  + Nói với người trịnh trọng/cấp trên: tự xưng là "tôi", gọi họ là "ngài/Tướng quân/tiền bối".
"""
        
        instruction = f"""
Bạn là một AI dịch thuật game chuyên nghiệp cho trò chơi Wuthering Waves (và các game nhập vai khác).
Nhiệm vụ của bạn là:
1. Phát hiện hộp hội thoại (dialogue box) hoặc khung mô tả chữ trong ảnh chụp màn hình game.
2. Trích xuất tên người nói (speaker) và đoạn hội thoại gốc tiếng Anh (original_text).
3. Dịch hội thoại đó sang tiếng Việt (translated_text) một cách tự nhiên, trôi chảy, đậm chất kiếm hiệp/khoa học viễn tưởng phù hợp với game Wuthering Waves.
4. Ngữ cảnh nhân vật chính (Rover):
   - Rover là {gender_desc}
   - Tham khảo kỹ lịch sử hội thoại gần đây để dịch đại từ xưng hô (anh, em, cô, tôi, ta, ngươi...) cho thống nhất và chính xác.
5. Danh sách thông tin về các nhân vật đã biết (hãy dựa vào đây để chọn đại từ xưng hô phù hợp):
{character_profiles}
6. Nếu nhân vật chưa có trong danh sách trên, hãy phân tích đoạn hội thoại hiện tại hoặc hình dáng nhân vật nói chuyện trong ảnh để suy đoán giới tính của họ (male/female/unknown) và mối quan hệ (friendly/respectful/hostile/neutral) rồi điền vào 'inferred_speaker_gender' và 'inferred_relationship'.
7. Áp dụng quy tắc xưng hô nghiêm ngặt sau:
{pronoun_rules}
8. Tra cứu từ điển thuật ngữ chuyên ngành sau để dịch đúng và nhất quán các địa danh, khái niệm khoa học, kỹ năng, vật phẩm. Khi gặp các thuật ngữ tiếng Anh này, bắt buộc phải dịch sang tiếng Việt và để tên tiếng Anh gốc trong ngoặc đơn (Ví dụ: Jinzhou -> Kim Châu (Jinzhou)):
{glossary_str}
9. Nếu trong hội thoại xuất hiện thuật ngữ chuyên môn hoặc địa danh MỚI chưa có trong từ điển ở trên, bạn hãy tự dịch sang tiếng Việt theo quy tắc: dịch nghĩa tiếng Việt + để tên tiếng Anh trong ngoặc đơn, đồng thời xuất chúng ra trường 'new_terms' dưới dạng {{"Thuật ngữ Tiếng Anh": "Bản dịch Tiếng Việt (Thuật ngữ Tiếng Anh)"}}. Ví dụ: {{"Central Plains": "Bình nguyên Trung tâm (Central Plains)"}}.
10. Xác định tọa độ hộp hội thoại dưới dạng box_2d = [ymin, xmin, ymax, xmax] theo tỷ lệ từ 0 đến 1000.
11. Nếu KHÔNG có hội thoại nào hoặc không phát hiện chữ nào trong ảnh, hãy trả về các trường text rỗng và box_2d là [0, 0, 0, 0].
"""
        return instruction

    def request_gemini_translation(self, img, is_auto=True, crop_box=None):
        prompt = self.build_prompt()
        sys_inst = self.get_system_instruction()
        model_name = self.config.get("model_name", "gemini-2.5-flash")
        
        attempts = len(self.api_keys)
        last_error = None
        
        for _ in range(attempts):
            api_key = self.api_keys[self.current_key_idx]
            try:
                # Initialize client dynamically using current key
                client = genai.Client(api_key=api_key)
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=[img, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TranslationResult,
                        system_instruction=sys_inst,
                        temperature=0.2
                    )
                )
                
                result_json = json.loads(response.text)
                
                # If coordinates are [0,0,0,0] but we have translated text, and it's auto mode,
                # we place it near the bottom of the screen (default dialogue position).
                if is_auto and sum(result_json.get("box_2d", [0,0,0,0])) == 0 and result_json.get("translated_text"):
                    # Default dialogue box coordinates for 16:9 bottom center
                    result_json["box_2d"] = [700, 200, 920, 800]
                    
                return result_json
                
            except Exception as e:
                last_error = e
                print(f"\n[Xoay API Key] Lỗi với Key index {self.current_key_idx}: {e}")
                # Rotate to next key
                self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
                print(f"[Xoay API Key] Chuyển sang dùng Key index {self.current_key_idx}...")
                
        # If all keys failed
        return {
            "speaker": "Lỗi",
            "original_text": "",
            "translated_text": f"Tất cả API Key đều thất bại. Lỗi cuối cùng: {str(last_error)}",
            "box_2d": [750, 250, 900, 750]
        }

    def show_translating_indicator(self, text="Đang dịch..."):
        # Put in queue to display on main thread
        self.gui_queue.put(('show_indicator', text))

    def hide_translating_indicator(self):
        self.gui_queue.put(('hide_indicator', None))

    def process_translation_task(self, img, width, height, is_auto=True, crop_coords=None):
        self.show_translating_indicator()
        
        result = self.request_gemini_translation(img, is_auto=is_auto)
        
        self.hide_translating_indicator()
        
        speaker = result.get("speaker", "")
        original = result.get("original_text", "")
        translated = result.get("translated_text", "")
        box_2d = result.get("box_2d", [0, 0, 0, 0])
        inferred_gender = result.get("inferred_speaker_gender", "unknown")
        inferred_rel = result.get("inferred_relationship", "neutral")
        
        if not translated.strip():
            print("Không tìm thấy hội thoại cần dịch.")
            return
            
        # Update character memory if speaker is detected
        if speaker:
            self.update_character_memory(speaker, inferred_gender, inferred_rel)
            
        # Update glossary if new terms are detected
        new_terms = result.get("new_terms", {})
        if new_terms:
            self.update_glossary(new_terms)
            
        print(f"\n[Gốc] {speaker + ': ' if speaker else ''}{original}")
        print(f"[Dịch] {speaker + ': ' if speaker else ''}{translated}")
        
        # Log to file
        self.log_translation(speaker, original, translated)
        
        # Update context history
        self.update_history(speaker, translated)
        
        # Calculate pixel coordinates
        if is_auto:
            # box_2d is [ymin, xmin, ymax, xmax] (0-1000 scale)
            ymin, xmin, ymax, xmax = box_2d
            x1 = int(xmin * width / 1000)
            y1 = int(ymin * height / 1000)
            x2 = int(xmax * width / 1000)
            y2 = int(ymax * height / 1000)
        else:
            # Crop mode coordinates are relative to the screen selection
            cx1, cy1, cx2, cy2 = crop_coords
            x1, y1, x2, y2 = cx1, cy1, cx2, cy2
            
        # Put on GUI queue to render overlay
        self.gui_queue.put(('show_overlay', (x1, y1, x2, y2, speaker, translated, is_auto)))

    def trigger_auto_translation(self):
        print("\n[Alt+Q] Đang chụp màn hình...")
        try:
            img, width, height = self.capture_screen()
            # Start background thread for API call to keep GUI responsive
            t = threading.Thread(target=self.process_translation_task, args=(img, width, height, True))
            t.daemon = True
            t.start()
        except Exception as e:
            print(f"Lỗi chụp màn hình: {e}")

    def trigger_manual_crop(self):
        print("\n[?] Hãy chọn vùng cần dịch trên màn hình...")
        # Capture screen first
        try:
            img, width, height = self.capture_screen()
            self.gui_queue.put(('start_crop_selector', (img, width, height)))
        except Exception as e:
            print(f"Lỗi chụp màn hình: {e}")

    def run_cli_loop(self):
        print("\n" + "="*50)
        print(" ỨNG DỤNG DỊCH MÀN HÌNH WUTHERING WAVES ĐÃ SẴN SÀNG")
        print(" - Nhấn [Alt + Q] bất cứ lúc nào trong game để dịch hội thoại.")
        print(" - Gõ [?] vào terminal này rồi Enter để vẽ vùng dịch thủ công.")
        print(" - Gõ [exit] hoặc [q] để thoát ứng dụng.")
        print("="*50 + "\n")
        
        # Register global hotkey
        try:
            keyboard.add_hotkey('alt+q', self.trigger_auto_translation)
        except Exception as e:
            print(f"Cảnh báo: Không thể đăng ký phím tắt toàn hệ thống Alt+Q: {e}")
            print("Gợi ý: Hãy thử chạy Terminal dưới quyền Administrator.")
            
        while True:
            try:
                cmd = input("wuwa-trans> ").strip()
                if cmd == '?':
                    self.trigger_manual_crop()
                elif cmd.lower() in ['exit', 'q']:
                    self.gui_queue.put(('exit', None))
                    break
                elif cmd.lower() == 'clear':
                    self.history = []
                    print("Đã xóa lịch sử hội thoại.")
                elif cmd:
                    print("Lệnh không hợp lệ. Gõ '?' để dịch vùng chọn, hoặc 'exit' để thoát.")
            except KeyboardInterrupt:
                self.gui_queue.put(('exit', None))
                break

class TranslationOverlay(tk.Toplevel):
    def __init__(self, parent, x1, y1, x2, y2, speaker, translated_text, duration, is_auto=True, use_fixed=True):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Transparent background styling
        self.normal_alpha = 0.85
        self.hover_alpha = 0.10
        self.attributes("-alpha", self.normal_alpha)
        
        bg_color = "#121212"
        self.configure(bg=bg_color)
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        # Position logic
        if is_auto and use_fixed:
            # Fixed subtitle at bottom center
            width = int(screen_w * 0.6)  # 60% of screen width
            if width < 600:
                width = 600
            height = 145
            x = (screen_w - width) // 2
            y = screen_h - height - 85   # offset by 85px to stay clear of taskbar/game UI
        else:
            # Custom coordinates (crop mode or floating mode)
            width = x2 - x1
            height = y2 - y1
            
            # Ensure minimum size for readability
            if width < 380:
                mid_x = (x1 + x2) // 2
                width = 450
                x1 = mid_x - width // 2
            if height < 90:
                mid_y = (y1 + y2) // 2
                height = 110
                y1 = mid_y - height // 2
                
            x = max(0, min(x1, screen_w - width))
            y = max(0, min(y1, screen_h - height))
            
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Apply Click-Through (Windows only)
        self.make_click_through()
        
        # UI labels
        self.spk_label = None
        if speaker and speaker.strip() != "":
            self.spk_label = tk.Label(self, text=speaker.upper(), font=("Segoe UI", 12, "bold"), fg="#FFD700", bg=bg_color, anchor="w")
            self.spk_label.pack(fill="x", padx=18, pady=(10, 2))
            
        self.txt_label = tk.Label(self, text=translated_text, font=("Segoe UI", 14), fg="#FFFFFF", bg=bg_color, wraplength=width-36, justify="left", anchor="nw")
        self.txt_label.pack(fill="both", expand=True, padx=18, pady=(2, 8))
        
        # Bind hover events for fading out
        self.bind("<Enter>", self.on_hover_enter)
        self.bind("<Leave>", self.on_hover_leave)
        if self.spk_label:
            self.spk_label.bind("<Enter>", self.on_hover_enter)
            self.spk_label.bind("<Leave>", self.on_hover_leave)
        self.txt_label.bind("<Enter>", self.on_hover_enter)
        self.txt_label.bind("<Leave>", self.on_hover_leave)
        
        # Auto-dismiss / fade
        self.duration_ms = duration * 1000
        self.after(self.duration_ms, self.fade_out)
        
    def on_hover_enter(self, event):
        # Hovered: make it almost completely transparent (10% opacity) so the user can see text behind it
        self.attributes("-alpha", self.hover_alpha)
        
    def on_hover_leave(self, event):
        # Unhovered: restore normal opacity
        self.attributes("-alpha", self.normal_alpha)
        
    def make_click_through(self):
        try:
            hwnd = self.winfo_id()
            import ctypes
            parent_hwnd = ctypes.windll.user32.GetParent(hwnd)
            target_hwnd = parent_hwnd if parent_hwnd else hwnd
            
            # Set WS_EX_TRANSPARENT (0x20) and WS_EX_LAYERED (0x80000)
            style = ctypes.windll.user32.GetWindowLongW(target_hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(target_hwnd, -20, style | 0x20 | 0x80000)
        except Exception as e:
            # Silent fail on non-Windows
            pass

    def fade_out(self):
        try:
            alpha = float(self.attributes("-alpha"))
            # Make sure we don't fade out if the user is currently hovering over it!
            # If mouse is over the window, we delay the fade out.
            current_mouse_alpha = float(self.attributes("-alpha"))
            if current_mouse_alpha == self.hover_alpha:
                # User is hovering, delay fade out by 2 seconds
                self.after(2000, self.fade_out)
                return
                
            if alpha > 0.05:
                self.attributes("-alpha", alpha - 0.05)
                self.after(40, self.fade_out)
            else:
                self.destroy()
        except tk.TclError:
            pass

class CropSelector(tk.Toplevel):
    def __init__(self, parent, screenshot, callback):
        super().__init__(parent)
        self.screenshot = screenshot
        self.callback = callback
        
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        
        self.width = self.winfo_screenwidth()
        self.height = self.winfo_screenheight()
        
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, cursor="cross")
        self.canvas.pack(fill="both", expand=True)
        
        # Darken screenshot for selection context
        dark_img = Image.blend(self.screenshot, Image.new("RGB", self.screenshot.size, (0,0,0)), 0.6)
        self.tk_img = ImageTk.PhotoImage(dark_img)
        self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
        
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.focus_force()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="#FFD700", width=2)

    def on_move_press(self, event):
        cur_x, cur_y = event.x, event.y
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = event.x, event.y
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        self.destroy()
        
        if (x2 - x1) > 10 and (y2 - y1) > 10:
            cropped = self.screenshot.crop((x1, y1, x2, y2))
            self.callback((x1, y1, x2, y2), cropped)

class TranslatingIndicator(tk.Toplevel):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9)
        self.configure(bg="#222222")
        
        # Center bottom of screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        w, h = 180, 40
        x = (screen_w - w) // 2
        y = screen_h - 100
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        lbl = tk.Label(self, text=text, font=("Segoe UI", 11, "bold"), fg="#FFD700", bg="#222222")
        lbl.pack(fill="both", expand=True)

def main():
    app = ScreenTranslatorApp()
    
    # GUI Manager
    root = tk.Tk()
    root.withdraw() # Hide the main root window
    
    # Process queue messages
    def check_queue():
        try:
            while True:
                msg_type, data = app.gui_queue.get_nowait()
                
                if msg_type == 'exit':
                    root.destroy()
                    os._exit(0)
                    
                elif msg_type == 'show_indicator':
                    if app.translating_indicator:
                        app.translating_indicator.destroy()
                    app.translating_indicator = TranslatingIndicator(root, data)
                    
                elif msg_type == 'hide_indicator':
                    if app.translating_indicator:
                        app.translating_indicator.destroy()
                        app.translating_indicator = None
                        
                elif msg_type == 'show_overlay':
                    # Destroy current overlay if active
                    if app.current_overlay:
                        app.current_overlay.destroy()
                        
                    x1, y1, x2, y2, speaker, translated, is_auto = data
                    dur = app.config.get("overlay_duration_seconds", 8)
                    use_fixed = app.config.get("use_fixed_subtitle", True)
                    app.current_overlay = TranslationOverlay(root, x1, y1, x2, y2, speaker, translated, dur, is_auto, use_fixed)
                    
                elif msg_type == 'start_crop_selector':
                    img, w, h = data
                    def on_crop_done(coords, cropped_img):
                        # Start background thread to translate cropped region
                        t = threading.Thread(target=app.process_translation_task, args=(cropped_img, w, h, False, coords))
                        t.daemon = True
                        t.start()
                    CropSelector(root, img, on_crop_done)
                    
                app.gui_queue.task_done()
        except queue.Empty:
            pass
        root.after(100, check_queue)

    # Start CLI loop in background thread
    t_cli = threading.Thread(target=app.run_cli_loop)
    t_cli.daemon = True
    t_cli.start()
    
    # Start checking queue
    root.after(100, check_queue)
    
    # Run Tkinter main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
