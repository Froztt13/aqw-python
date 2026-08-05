import subprocess
import sys
import os
import shutil

def main():
    print("Building Eclipse Bot Windows standalone executable...")
    
    app_name = "Eclipse_Bot"
    entrypoint = "eclipse_gui.py"
    
    # Try to terminate any running instance of the app to avoid file lock issues
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", f"{app_name}.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # Clean output directories if they exist
    for path in [
        os.path.join("build", app_name),
        os.path.join("dist", app_name),
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
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=" + app_name,
        "--onefile",
        "--noconsole",
        "--noconfirm",
        "--clean",
        "--add-data=web_eclipse;web_eclipse",
        "--add-data=bot;bot",
        "--icon=eclipse_app.ico",
        entrypoint
    ]
    
    print("Executing command: " + " ".join(cmd))
    result = subprocess.run(cmd)
    
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
