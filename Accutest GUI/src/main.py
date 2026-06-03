import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from main_window import MainWindow
from style import apply_style
from utils import resource_path, set_windows_app_id


def main():
    set_windows_app_id()
    app = QApplication(sys.argv)
    
    # Look for logo in assets folder (parent directory)
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "Logo.ico")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))
    
    apply_style(app)
    w = MainWindow()
    if os.path.exists(logo_path):
        w.setWindowIcon(QIcon(logo_path))
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
