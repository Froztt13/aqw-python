import subprocess
import sys
import os
import shutil

def main():
    print("Building Slavery Bot Windows standalone executable...")
    
    app_name = "Slavery_Bot"
    entrypoint = "slavery_gui.py"
    
    # Clean output directories if they exist
    for path in [
        os.path.join("build", app_name),
        os.path.join("dist", f"{app_name}.exe")
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

    # Build command for PyInstaller on Windows
    # Windows uses ";" as path separator for --add-data instead of ":"
    cmd = [
        "pyinstaller",
        "--name=" + app_name,
        "--noconsole",
        "--noconfirm",
        "--clean",
        "--add-data=web_slavery;web_slavery",
        "--add-data=bot;bot",
        "--icon=app.ico",
        entrypoint
    ]
    
    print("Executing command: " + " ".join(cmd))
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("\n" + "="*50)
        print("SUCCESS! Windows standalone executable built successfully.")
        print(f"You can find the standalone exe at: {os.path.abspath(f'dist/{app_name}.exe')}")
        print("="*50 + "\n")
    else:
        print("\nERROR! PyInstaller build failed.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
