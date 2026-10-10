import subprocess
import sys
import os
import shutil

# Determine project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_windows_icon():
    png_path = os.path.join(project_root, "app", "web_dashboard", "temple_icon.png")
    ico_path = os.path.join(project_root, "app.ico")
    if os.path.exists(png_path) and not os.path.exists(ico_path):
        try:
            from PIL import Image
            img = Image.open(png_path)
            img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print("Successfully generated app.ico on Windows.")
        except Exception as e:
            print(f"Note: Could not generate app.ico: {e}")

def build_windows():
    print("Building AQW Bot Hub Windows standalone executable (.exe)...")
    
    app_name = "AQW_Bot_Hub"
    entrypoint = os.path.join(project_root, "app", "build_hub_app.py")
    
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

    generate_windows_icon()

    # Detect python / pyinstaller executable
    pyinstaller_bin = [sys.executable, "-m", "PyInstaller"]
    venv_pyinstaller = os.path.join(project_root, "venv", "Scripts", "pyinstaller.exe")
    if os.path.exists(venv_pyinstaller):
        pyinstaller_bin = [venv_pyinstaller]

    cmd = pyinstaller_bin + [
        f"--name={app_name}",
        "--onefile",
        "--noconsole",
        "--noconfirm",
        "--clean",
        f"--paths={project_root}",
        "app/web_dashboard;web_dashboard",
        "bot;bot",
        "--hidden-import=psutil"
    ]
    # Format add-data correctly
    cmd[6] = f"--add-data={os.path.join('app', 'web_dashboard')};web_dashboard"
    cmd[7] = f"--add-data=bot;bot"
    
    ico_file = os.path.join(project_root, "app.ico")
    if os.path.exists(ico_file):
        cmd.append(f"--icon={ico_file}")
    else:
        print("Warning: Icon file 'app.ico' not found. Building without icon.")
        
    cmd.append(entrypoint)
    
    print("\nExecuting command:\n" + " ".join(cmd) + "\n")
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        print("\n" + "="*50)
        print("SUCCESS! Windows standalone executable built successfully.")
        output_exe = os.path.join(project_root, "dist", f"{app_name}.exe")
        print(f"You can find the standalone exe at: {os.path.abspath(output_exe)}")
        print("="*50 + "\n")
    else:
        print("\nERROR! PyInstaller Windows build failed.")
        sys.exit(result.returncode)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        # Launch GUI on Windows
        sys.path.insert(0, project_root)
        from app.build_hub_app import run_gui
        run_gui()
    else:
        # Default behavior: build Windows .exe
        build_windows()

if __name__ == "__main__":
    main()
