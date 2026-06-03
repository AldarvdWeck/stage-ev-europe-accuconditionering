from PySide6.QtWidgets import QComboBox, QLabel
from PySide6.QtCore import Qt

class ArrowComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arrow_label = QLabel("▾", self)
        self.arrow_label.setStyleSheet("color: #6b7280; font-size: 12px; background: transparent;")
        self.arrow_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.arrow_label.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.arrow_label.adjustSize()
        x = self.width() - self.arrow_label.width() - 10
        y = (self.height() - self.arrow_label.height()) // 2
        self.arrow_label.move(x, y)