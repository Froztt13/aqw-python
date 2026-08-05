import subprocess
import sys
import os
import shutil

def main():
    print("Building AQW Bot macOS app bundle...")
    
    app_name = "AQW_Bot"
    entrypoint = "gui.py"
    
    # Ensure specific build/dist outputs are clean without wiping other apps in dist/
    for path in [
        os.path.join("build", app_name),
        os.path.join("dist", f"{app_name}.app")
    ]:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"Cleaned existing {path}.")
            except Exception as e:
                print(f"Warning: Could not clean {path}: {e}")

    # Build command for PyInstaller
    # --add-data "web:web" copies the frontend web assets into the bundle
    # --windowed creates a macOS .app bundle instead of a command-line binary
    cmd = [
        "venv/bin/pyinstaller",
        "--name=" + app_name,
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data=web:web",
        "--icon=app.icns",
        entrypoint
    ]
    
    print("Executing command: " + " ".join(cmd))
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "="*50)
        print("SUCCESS! macOS App Bundle built successfully.")
        print(f"You can find the double-clickable app at: {os.path.abspath(f'dist/{app_name}.app')}")
        print("="*50 + "\n")
    else:
        print("\nERROR! PyInstaller build failed.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
