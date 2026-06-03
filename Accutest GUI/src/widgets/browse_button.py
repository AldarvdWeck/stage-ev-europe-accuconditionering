from PySide6.QtWidgets import QPushButton

class BrowseButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self._selected_text = ""

    def set_selected_text(self, text: str):
        self._selected_text = text
        if self._selected_text:
            self.setText(self._selected_text)
        else:
            self.setText("Bladeren")

    def enterEvent(self, event):
        self.setText("Bladeren")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._selected_text:
            self.setText(self._selected_text)
        else:
            self.setText("Bladeren")
        super().leaveEvent(event)