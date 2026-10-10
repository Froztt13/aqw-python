import subprocess
import sys
import os
import shutil

# Determine project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_windows_icon():
    slavery_ico = os.path.join(project_root, "app", "web_dashboard", "slavery", "app.ico")
    if os.path.exists(slavery_ico):
        return slavery_ico

    png_path = os.path.join(project_root, "app", "web_dashboard", "slavery", "app_icon.png")
    ico_path = os.path.join(project_root, "slavery_app.ico")
    if os.path.exists(png_path) and not os.path.exists(ico_path):
        try:
            from PIL import Image
            img = Image.open(png_path)
            img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print("Successfully generated slavery_app.ico on Windows.")
            return ico_path
        except Exception as e:
            print(f"Note: Could not generate slavery_app.ico: {e}")
    return os.path.join(project_root, "app.ico")

def build_windows(enable_console=False):
    print("Building AQW Maid Slavery Windows standalone executable (.exe)...")
    
    app_name = "AQW_Maid_Slavery"
    entrypoint = os.path.join(project_root, "app", "build_slavery_app.py")
    
    # Try to terminate any running instance of the app to avoid file lock issues on Windows
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", f"{app_name}.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # Clean output directories if they exist
    for path in [
        os.path.join(project_root, "build", app_name),
        os.path.join(project_root, "dist", app_name),
        os.path.join(project_root, "dist", f"{app_name}.exe")
    ]:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                print(f"Cleaned existing {path}.")
            except Exception as e:
                print(f"Warning: Could not clean {path}: {e}")

    ico_file = generate_windows_icon()

    # Detect python / pyinstaller executable
    pyinstaller_bin = [sys.executable, "-m", "PyInstaller"]
    venv_pyinstaller = os.path.join(project_root, "venv", "Scripts", "pyinstaller.exe")
    if os.path.exists(venv_pyinstaller):
        pyinstaller_bin = [venv_pyinstaller]

    web_dashboard_src = os.path.join("app", "web_dashboard")
    cmd = pyinstaller_bin + [
        f"--name={app_name}",
        "--onefile",
        "--noconfirm",
        "--clean",
        f"--paths={project_root}",
        f"--add-data={web_dashboard_src};web_dashboard",
        f"--add-data=bot;bot",
        f"--add-data=commands;commands",
        f"--add-data=abstracts;abstracts",
        f"--add-data=templates;templates",
        f"--add-data=bot_cmds;bot_cmds",
        "--collect-all=webview",
        "--collect-all=clr_loader",
        "--collect-all=pythonnet",
        "--hidden-import=psutil",
        "--hidden-import=bottle",
        "--hidden-import=clr",
        "--hidden-import=clr_loader",
        "--hidden-import=pythonnet",
        "--hidden-import=webview",
        "--hidden-import=webview.platforms.winforms",
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=commands",
        "--hidden-import=abstracts",
        "--hidden-import=templates",
        "--hidden-import=bot_cmds",
        "--hidden-import=handlers",
        "--hidden-import=model",
        "--hidden-import=core"
    ]
    
    if not enable_console:
        cmd.append("--noconsole")

    if os.path.exists(ico_file):
        cmd.append(f"--icon={ico_file}")
    else:
        print("Warning: Icon file not found. Building without icon.")
        
    cmd.append(entrypoint)
    
    print("\nExecuting command:\n" + " ".join(cmd) + "\n")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "="*60)
        output_file = os.path.join(project_root, "dist", f"{app_name}.exe")
        print("SUCCESS! Windows standalone executable built successfully.")
        print(f"You can find the .exe at: {os.path.abspath(output_file)}")
        print("="*60 + "\n")
    else:
        print("\nERROR! PyInstaller build failed.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    enable_console = "--console" in sys.argv
    build_windows(enable_console=enable_console)
