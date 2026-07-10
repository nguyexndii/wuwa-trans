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
:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :admin
) else (
    echo Yeu cau quyen Administrator...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
:admin
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
    
    # Escape paths for PowerShell strings
    shortcut_path_ps = shortcut_path.replace("\\", "\\\\")
    desktop_shortcut_path_ps = desktop_shortcut_path.replace("\\", "\\\\")
    target_path_ps = target_path.replace("\\", "\\\\")
    arguments_ps = arguments.replace("\\", "\\\\")
    project_dir_ps = project_dir.replace("\\", "\\\\")
    icon_location_ps = icon_location.replace("\\", "\\\\")
    
    ps_script = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    
    # Tao shortcut trong thu muc du an
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path_ps}")
    $Shortcut.TargetPath = "{target_path_ps}"
    $Shortcut.Arguments = '{arguments_ps}'
    $Shortcut.WorkingDirectory = "{project_dir_ps}"
    $Shortcut.IconLocation = "{icon_location_ps}"
    $Shortcut.Description = "Dich man hinh game Wuthering Waves"
    $Shortcut.Save()
    
    # Set Run as Admin flag (LinkFlags byte 21, bit 6)
    $bytes = [System.IO.File]::ReadAllBytes("{shortcut_path_ps}")
    $bytes[21] = $bytes[21] -bor 0x20
    [System.IO.File]::WriteAllBytes("{shortcut_path_ps}", $bytes)
    
    # Tao shortcut tren Desktop
    $DesktopShortcut = $WshShell.CreateShortcut("{desktop_shortcut_path_ps}")
    $DesktopShortcut.TargetPath = "{target_path_ps}"
    $DesktopShortcut.Arguments = '{arguments_ps}'
    $DesktopShortcut.WorkingDirectory = "{project_dir_ps}"
    $DesktopShortcut.IconLocation = "{icon_location_ps}"
    $DesktopShortcut.Description = "Dich man hinh game Wuthering Waves"
    $DesktopShortcut.Save()
    
    # Set Run as Admin flag for Desktop shortcut
    $bytes2 = [System.IO.File]::ReadAllBytes("{desktop_shortcut_path_ps}")
    $bytes2[21] = $bytes2[21] -bor 0x20
    [System.IO.File]::WriteAllBytes("{desktop_shortcut_path_ps}", $bytes2)
    """
    
    try:
        # Run PowerShell command
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        print("-> Da tao Shortcut (tu dong chay Admin) tai thu muc du an!")
        print("-> Da tao Shortcut (tu dong chay Admin) ngoai Desktop!")
        print("\n=== HOAN THANH SETUP ===")
        print("Bay gio ban co the:")
        print("1. Click dup vao file Run_Translator.bat hoac file Shortcut bat ky luc nao de chay ung dung duoi quyen Admin.")
        print("2. Click chuot phai vao file shortcut 'Wuthering Waves Translator' va chon 'Pin to taskbar' de ghim len Taskbar.")
    except Exception as e:
        print(f"Loi tao shortcut qua PowerShell: {e}")

if __name__ == "__main__":
    main()
