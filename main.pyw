import webview
import pystray
from PIL import Image, ImageDraw
import threading
import os
import sys
import ctypes
import socket

ICON_SIZE = 64
IPC_PORT = 17890

def _connect_and_show():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('127.0.0.1', IPC_PORT))
        s.sendall(b'show')
        s.close()
        return True
    except:
        return False

def _ipc_listener(win_ref, stop_event):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('127.0.0.1', IPC_PORT))
    except OSError:
        return
    s.listen(1)
    s.settimeout(1)
    while not stop_event.is_set():
        try:
            conn, _ = s.accept()
            data = conn.recv(1024)
            if data.strip() == b'show':
                w = win_ref()
                if w:
                    w.show()
                    w.restore()
            conn.close()
        except socket.timeout:
            continue
        except:
            pass
    s.close()

def _make_icon():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, ICON_SIZE - 2, ICON_SIZE - 2], fill=(255, 200, 0, 255))
    return img

def _tray_thread(win_ref, stop_event):
    def show():
        w = win_ref()
        if w: w.show()
    def quit():
        stop_event.set()
        w = win_ref()
        if w: w.destroy()
        os._exit(0)
    icon = pystray.Icon(
        "TaskFlow", _make_icon(), "TaskFlow",
        pystray.Menu(
            pystray.MenuItem("TaskFlowを開く", show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("終了", quit),
        ),
    )
    icon.run()

def main():
    ctypes.windll.kernel32.CreateMutexW(None, False, "TaskFlow_SingleInstance_Mutex")
    if ctypes.windll.kernel32.GetLastError() == 183:
        if _connect_and_show():
            sys.exit(0)
        hwnd = ctypes.windll.user32.FindWindowW(None, "TaskFlow")
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        sys.exit(0)

    stop = threading.Event()

    base_path = os.path.dirname(os.path.abspath(__file__))
    index_path = 'file:///' + os.path.join(base_path, 'index.html').replace('\\', '/')

    class Api:
        def __init__(self):
            self.base = os.path.dirname(os.path.abspath(__file__))
        def get_old_data(self):
            path = os.path.join(self.base, 'default.json')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            return None

    window = webview.create_window(
        "TaskFlow", index_path,
        width=1200, height=800,
        js_api=Api()
    )
    win_ref = lambda: window

    def on_closing():
        window.hide()
        return False

    window.events.closing += on_closing

    ipc_stop = threading.Event()
    ipc_thread = threading.Thread(target=_ipc_listener, args=(win_ref, ipc_stop), daemon=True)
    ipc_thread.start()

    t = threading.Thread(target=_tray_thread, args=(win_ref, stop), daemon=True)
    t.start()

    webview.start(gui=None, debug=False)

if __name__ == "__main__":
    main()
