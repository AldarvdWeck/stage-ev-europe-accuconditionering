import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QFileDialog, QVBoxLayout, QLabel, QFrame, QSizePolicy
from icons import pixmap_from_svg

class FileDropButton(QPushButton):
    def __init__(
        self,
        icon_svg: str,
        label_text: str,
        select_mode: str = "file",
        icon_size: int = 70,
        hint_text: str = "Klik om te kiezen of sleep hierheen",
        placeholder_text: str = "Geen bestand geselecteerd",
        parent=None
    ):
        super().__init__(parent)
        self.setObjectName("fileDropButton")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumWidth(0)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setText("")
        self.select_mode = select_mode
        self.placeholder_text = placeholder_text
        self.setToolTip("Klik om te kiezen of sleep hierheen")
        self.clicked.connect(self.open_file_dialog)
        self.selected_file = ""
        self.file_selected_callback = None

        button_layout = QVBoxLayout(self)
        button_layout.setContentsMargins(14, 12, 14, 12)
        button_layout.setSpacing(5)
        button_layout.addStretch(1)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.icon_label.setPixmap(
            pixmap_from_svg(icon_svg).scaled(
                icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

        self.text_label = QLabel(label_text)
        self.text_label.setObjectName("fileDropButtonTitle")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.hint_label = QLabel(hint_text)
        self.hint_label.setObjectName("fileDropButtonHint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setWordWrap(True)
        self.hint_label.setMinimumHeight(34)
        self.hint_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.selected_chip = QFrame()
        self.selected_chip.setObjectName("fileSelectedChip")
        self.selected_chip.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        selected_chip_layout = QVBoxLayout(self.selected_chip)
        selected_chip_layout.setContentsMargins(10, 5, 10, 5)

        self.selected_label = QLabel(self.placeholder_text)
        self.selected_label.setObjectName("fileSelectedText")
        self.selected_label.setAlignment(Qt.AlignCenter)
        self.selected_label.setWordWrap(False)
        self.selected_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.selected_chip.setMinimumHeight(34)
        selected_chip_layout.addWidget(self.selected_label)

        button_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.text_label, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.hint_label, alignment=Qt.AlignCenter)
        button_layout.addStretch(1)
        button_layout.addWidget(self.selected_chip)

    def open_file_dialog(self):
        if self.select_mode == "folder":
            selected_path = QFileDialog.getExistingDirectory(
                self,
                "Kies map",
                os.path.expanduser("~")
            )
        else:
            selected_path, _ = QFileDialog.getOpenFileName(
                self,
                "Kies bestand",
                os.path.expanduser("~"),
                "Data bestanden (*.csv *.txt);;Alle bestanden (*.*)"
            )

        if selected_path:
            self.set_selected_file(selected_path)

    def set_selected_file(self, file_path: str):
        self.selected_file = file_path
        self.setProperty("selected", True)
        self.selected_chip.setProperty("selected", True)
        self.selected_label.setProperty("selected", True)
        for widget in (self, self.selected_chip, self.selected_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        if self.file_selected_callback:
            self.file_selected_callback(file_path)

    def set_selected_display_text(self, text: str):
        self.selected_label.setText(text if text else self.placeholder_text)
        self.selected_label.setToolTip(text)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)

        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path:
                self.set_selected_file(file_path)
                event.acceptProposedAction()
                return

        event.ignore()
