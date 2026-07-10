import os
import subprocess
from PIL import Image

def main():
    print("Bat dau cai dat phim tat va bieu tuong...")
    
    # 1. Chuyen doi file PNG sang ICO
    src_png = r"C:\Users\Diiexe\.gemini\antigravity\brain\d9065efa-2283-4cd2-959c-95724bea90cb\wuwa_trans_icon_1783679831010.png"
    dest_ico = "icon.ico"
    
    if os.path.exists(src_png):
        try:
            img = Image.open(src_png)
            # Luu thanh ICO voi nhieu kich thuoc tieu chuan
            img.save(dest_ico, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print("-> Da tao file icon.ico tu anh logo!")
        except Exception as e:
            print(f"Loi tao icon.ico: {e}")
    else:
        print(f"Khong tim thay file nguon PNG tai: {src_png}")
        
    # 2. Tao file Run_Translator.bat
    bat_content = """@echo off
cd /d "%~dp0"
title Wuthering Waves Screen Translator
echo Dang khoi dong ung dung dich...
.venv\\Scripts\\python.exe main.py
pause
"""
    with open("Run_Translator.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    print("-> Da tao file Run_Translator.bat!")
    
    # 3. Tao Shortcut dung PowerShell
    project_dir = os.path.abspath(os.path.dirname(__file__))
    shortcut_path = os.path.join(project_dir, "Wuthering Waves Translator.lnk")
    desktop_shortcut_path = os.path.join(os.path.expanduser("~"), "Desktop", "Wuthering Waves Translator.lnk")
    
    # Target: cmd.exe /c "Run_Translator.bat" - this is pinnable to taskbar!
    target_path = "cmd.exe"
    bat_path = os.path.join(project_dir, "Run_Translator.bat")
    arguments = f'/c ""{bat_path}""'
    icon_location = os.path.join(project_dir, "icon.ico")
    
    ps_script = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    
    # Tao shortcut trong thu muc du an
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{target_path}"
    $Shortcut.Arguments = '{arguments}'
    $Shortcut.WorkingDirectory = "{project_dir}"
    $Shortcut.IconLocation = "{icon_location}"
    $Shortcut.Description = "Dich man hinh game Wuthering Waves"
    $Shortcut.Save()
    
    # Tao shortcut tren Desktop
    $DesktopShortcut = $WshShell.CreateShortcut("{desktop_shortcut_path}")
    $DesktopShortcut.TargetPath = "{target_path}"
    $DesktopShortcut.Arguments = '{arguments}'
    $DesktopShortcut.WorkingDirectory = "{project_dir}"
    $DesktopShortcut.IconLocation = "{icon_location}"
    $DesktopShortcut.Description = "Dich man hinh game Wuthering Waves"
    $DesktopShortcut.Save()
    """
    
    try:
        # Run PowerShell command
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        print("-> Da tao Shortcut tai thu muc du an!")
        print("-> Da tao Shortcut ngoai Desktop!")
        print("\n=== HOAN THANH SETUP ===")
        print("Bay gio ban co the:")
        print("1. Click dup vao file Run_Translator.bat de chay.")
        print("2. Hoac Click chuot phai vao file shortcut 'Wuthering Waves Translator' ngoai Desktop / thu muc du an va chon 'Pin to taskbar' (Ghim vao thanh tac vu) de ghim.")
    except Exception as e:
        print(f"Loi tao shortcut qua PowerShell: {e}")

if __name__ == "__main__":
    main()
