import os
import sys

# Patch certifi path inside frozen app bundles before other imports
if getattr(sys, 'frozen', False):
    try:
        import certifi
        import certifi.core
        def patched_where():
            meipass_cacert = os.path.join(getattr(sys, '_MEIPASS', ''), 'certifi', 'cacert.pem')
            if os.path.exists(meipass_cacert):
                return meipass_cacert
            resources_cacert = os.path.join(os.path.dirname(sys.executable), '..', 'Resources', 'certifi', 'cacert.pem')
            if os.path.exists(resources_cacert):
                return os.path.abspath(resources_cacert)
            frameworks_cacert = os.path.join(os.path.dirname(sys.executable), '..', 'Frameworks', 'certifi', 'cacert.pem')
            if os.path.exists(frameworks_cacert):
                return os.path.abspath(frameworks_cacert)
            return meipass_cacert
        certifi.core.where = patched_where
        certifi.where = patched_where
        os.environ['SSL_CERT_FILE'] = patched_where()
        os.environ['REQUESTS_CA_BUNDLE'] = patched_where()
    except Exception as e:
        print(f"Warning: certifi patch failed: {e}")

import json
import time
import asyncio
import threading
from datetime import datetime
import socket
import re
import html
import subprocess
import shutil
import platform

def get_project_root():
    if getattr(sys, 'frozen', False):
        contents_dir = os.path.dirname(os.path.dirname(sys.executable))
        app_dir = os.path.dirname(contents_dir)
        parent_dir = os.path.dirname(app_dir)
        grandparent_dir = os.path.dirname(parent_dir)
        
        for path in [grandparent_dir, parent_dir, os.getcwd()]:
            if os.path.exists(os.path.join(path, "bot")):
                return os.path.abspath(path)
        return os.path.abspath(grandparent_dir)
    else:
        # Located in /project_root/app/build_slavery_app.py
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

project_root = get_project_root()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if getattr(sys, 'frozen', False):
    resources_dir = getattr(sys, '_MEIPASS', None)
    if resources_dir and resources_dir not in sys.path:
        sys.path.insert(0, resources_dir)

from bottle import Bottle, static_file
import webview

from app.build_hub_app import (
    SlaveryApi,
    cleanup_orphaned_processes,
    find_free_port,
    unified_redirector_out,
    unified_redirector_err
)

def start_local_server(web_dashboard_dir, web_slavery_dir):
    app = Bottle()

    @app.route('/')
    @app.route('/index.html')
    def serve_index():
        return static_file('index.html', root=web_slavery_dir)

    @app.route('/components.js')
    def serve_components():
        return static_file('components.js', root=web_dashboard_dir)

    @app.route('/slavery/<path:path>')
    def serve_slavery_subpath(path):
        return static_file(path, root=web_slavery_dir)

    @app.route('/<path:path>')
    def serve_static(path):
        if path == 'components.js':
            return static_file('components.js', root=web_dashboard_dir)
        file_in_slavery = os.path.join(web_slavery_dir, path)
        if os.path.exists(file_in_slavery):
            return static_file(path, root=web_slavery_dir)
        return static_file(path, root=web_dashboard_dir)

    port = find_free_port()
    t = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=port, quiet=True))
    t.daemon = True
    t.start()
    return f"http://127.0.0.1:{port}"

def run_gui():
    cleanup_orphaned_processes()

    # Windows Edge WebView2 verification
    if platform.system() == "Windows":
        try:
            from webview.platforms import winforms
            if not winforms._is_chromium():
                import ctypes
                msg = (
                    "Aplikasi AQW Maid Slavery memerlukan 'Microsoft Edge WebView2 Runtime' agar dapat berjalan di Windows.\n\n"
                    "Di perangkat ini WebView2 Runtime belum terdeteksi. Silakan unduh dan pasang WebView2 Runtime dari situs resmi Microsoft:\n"
                    "https://developer.microsoft.com/en-us/microsoft-edge/webview2/\n\n"
                    "Klik OK untuk membuka halaman unduhan resmi Microsoft."
                )
                res = ctypes.windll.user32.MessageBoxW(0, msg, "Microsoft Edge WebView2 Diperlukan", 0x30 | 0x1)
                if res == 1:
                    import webbrowser
                    webbrowser.open("https://go.microsoft.com/fwlink/p/?LinkId=2124703")
                sys.exit(1)
        except Exception:
            pass

    slavery_api = SlaveryApi()

    # Register stream redirection directly to Slavery System logs tab
    unified_redirector_out.standalone_callback = slavery_api.handle_slave_log
    unified_redirector_err.standalone_callback = slavery_api.handle_slave_log

    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', '')
        web_dashboard_dir = os.path.join(base_path, 'web_dashboard')
    else:
        web_dashboard_dir = os.path.join(project_root, 'app', 'web_dashboard')

    web_slavery_dir = os.path.join(web_dashboard_dir, 'slavery')

    print(f"Loading Slavery GUI assets from: {web_slavery_dir}")
    url = start_local_server(web_dashboard_dir, web_slavery_dir)
    print(f"Slavery Bot server running at: {url}")

    window = webview.create_window(
        title='AQW Maid Slavery',
        url=url,
        js_api=slavery_api,
        width=1280,
        height=850,
        min_size=(1020, 700),
        resizable=True
    )

    slavery_api.set_window(window)

    webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False

    storage_path = os.path.expanduser("~/.aqw_bot/webview_slavery")
    os.makedirs(storage_path, exist_ok=True)

    def on_closed():
        print("Slavery Bot application closing, terminating active bot threads...")
        try:
            slavery_api.stop_slaves()
        except Exception:
            pass
        try:
            import psutil
            current_process = psutil.Process(os.getpid())
            for child in current_process.children(recursive=True):
                try:
                    child.kill()
                except Exception:
                    pass
        except Exception:
            pass
        os._exit(0)

    window.events.closed += on_closed

    try:
        webview.start(debug=True, private_mode=False, storage_path=storage_path)
    finally:
        on_closed()

def generate_icons():
    system = platform.system()
    png_path = os.path.join(project_root, "app", "web_dashboard", "slavery", "app_icon.png")
    if not os.path.exists(png_path):
        png_path = os.path.join(project_root, "app", "web_dashboard", "temple_icon.png")
    if not os.path.exists(png_path):
        return

    print("Generating application icons for Slavery Bot...")
    if system == "Darwin":
        try:
            iconset_dir = "slavery_app.iconset"
            os.makedirs(iconset_dir, exist_ok=True)
            sizes = [16, 32, 64, 128, 256, 512, 1024]
            for size in sizes:
                out_path1 = os.path.join(iconset_dir, f"icon_{size}x{size}.png")
                subprocess.run(["sips", "-z", str(size), str(size), png_path, "--out", out_path1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if size * 2 in sizes:
                    out_path2 = os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png")
                    subprocess.run(["sips", "-z", str(size*2), str(size*2), png_path, "--out", out_path2], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            subprocess.run(["iconutil", "-c", "icns", iconset_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            shutil.rmtree(iconset_dir)
            print("Successfully generated slavery_app.icns on macOS.")
        except Exception as e:
            print(f"Failed to generate slavery_app.icns: {e}")

    elif system == "Windows":
        try:
            from PIL import Image
            img = Image.open(png_path)
            img.save("slavery_app.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print("Successfully generated slavery_app.ico on Windows.")
        except Exception as e:
            print(f"Failed to generate Windows slavery_app.ico: {e}")

def build_app():
    app_name = "AQW_Maid_Slavery"
    entrypoint = os.path.join("app", "build_slavery_app.py")

    generate_icons()
    print("Building AQW Maid Slavery macOS app bundle (.app)...")

    outputs_to_clean = [
        os.path.join("build", app_name),
        os.path.join("dist", f"{app_name}.app"),
        os.path.join("dist", app_name)
    ]

    for path in outputs_to_clean:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                print(f"Cleaned existing {path}.")
            except Exception as e:
                print(f"Failed to clean {path}: {e}")

    data_folders = [
        ("app/web_dashboard", "web_dashboard"),
        ("bot", "bot"),
        ("commands", "commands"),
        ("abstracts", "abstracts"),
        ("templates", "templates"),
        ("bot_cmds", "bot_cmds")
    ]

    icon_file = "slavery_app.icns"
    if not os.path.exists(icon_file):
        icon_file = "app.icns"

    pyinstaller_bin = "pyinstaller"
    venv_pyinstaller = os.path.join("venv", "bin", "pyinstaller")
    if os.path.exists(venv_pyinstaller):
        pyinstaller_bin = venv_pyinstaller

    cmd = [
        pyinstaller_bin,
        f"--name={app_name}",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--collect-all=webview",
        "--hidden-import=psutil",
        "--hidden-import=bottle",
        "--hidden-import=webview",
        "--hidden-import=commands",
        "--hidden-import=abstracts",
        "--hidden-import=templates",
        "--hidden-import=bot_cmds",
        "--hidden-import=handlers",
        "--hidden-import=model",
        "--hidden-import=core",
        f"--paths={project_root}"
    ]

    for src, dest in data_folders:
        cmd.append(f"--add-data={src}:{dest}")

    if os.path.exists(icon_file):
        cmd.append(f"--icon={icon_file}")
    else:
        print(f"Warning: Icon file '{icon_file}' not found. Building without icon.")

    cmd.append(entrypoint)

    print("\nExecuting command:\n" + " ".join(cmd) + "\n")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "="*60)
        output_file_desc = os.path.join("dist", f"{app_name}.app")
        print("SUCCESS! macOS App bundle for Slavery Bot built successfully.")
        print(f"You can find the standalone client at: {os.path.abspath(output_file_desc)}")
        print("="*60 + "\n")
    else:
        print("\nERROR! PyInstaller build failed.")
        sys.exit(result.returncode)

def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] in ("build", "--build"):
            build_app()
        else:
            run_gui()
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"[AQW Maid Slavery] Critical startup exception:\n{err_msg}")
        try:
            log_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "slavery_crash.log"), "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
