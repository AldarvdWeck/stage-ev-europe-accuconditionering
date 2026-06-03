import sys
import os
from serial.tools import list_ports
from config import WINDOWS_APP_ID

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def set_windows_app_id():
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WINDOWS_APP_ID)
    except Exception:
        pass

def find_arduino_port():
    ports = list(list_ports.comports())

    for p in ports:
        desc = (p.description or "").lower()
        manu = (p.manufacturer or "").lower()

        if any(k in desc for k in ["arduino", "ch340", "usb serial", "usb-serial"]) or \
           any(k in manu for k in ["arduino", "wch"]):
            return p.device

    if len(ports) == 1:
        return ports[0].device

    return None

def list_serial_ports():
    ports = list(list_ports.comports())
    return [p.device for p in ports]
