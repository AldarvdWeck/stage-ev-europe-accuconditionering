import os
import csv
import math
import time
from datetime import datetime
from pathlib import Path

import serial
from serial.tools import list_ports

from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtGui import QDoubleValidator, QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, QLabel, QFrame, QGridLayout, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLineEdit, QStackedWidget, QSizePolicy
)

from config import (
    PLOT_UPDATE_HZ, PLOT_UPDATE_INTERVAL_S, BAUD, SAMPLE_HZ, WINDOW_SECONDS,
    MAX_POINTS, MIN_Y_SPAN, RECONNECT_INTERVAL_S, RECONNECT_INTERVAL_MS
)
from utils import find_arduino_port, list_serial_ports
from icons import FILE_ICON_SVG, LIGHTNING_ICON_SVG
from widgets.arrow_combo_box import ArrowComboBox
from widgets.sensor_plot import SensorPlot
from widgets.browse_button import BrowseButton
from widgets.file_drop_button import FileDropButton

PAGE_TEMP_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
  <path d="M9.5 12.5a1.5 1.5 0 1 1-2-1.415V6.5a.5.5 0 0 1 1 0v4.585a1.5 1.5 0 0 1 1 1.415"/>
  <path d="M5.5 2.5a2.5 2.5 0 0 1 5 0v7.55a3.5 3.5 0 1 1-5 0zM8 1a1.5 1.5 0 0 0-1.5 1.5v7.987l-.167.15a2.5 2.5 0 1 0 3.333 0l-.166-.15V2.5A1.5 1.5 0 0 0 8 1"/>
</svg>"""

PAGE_GRAPH_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M0 0h1v15h15v1H0zm10 3.5a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-1 0V4.9l-3.613 4.417a.5.5 0 0 1-.74.037L7.06 6.767l-3.656 5.027a.5.5 0 0 1-.808-.588l4-5.5a.5.5 0 0 1 .758-.06l2.609 2.61L13.445 4H10.5a.5.5 0 0 1-.5-.5"/>
</svg>"""



GEAR_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-gear-fill" viewBox="0 0 16 16">
  <path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"/>
</svg>"""

PLAY_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-play-fill" viewBox="0 0 16 16">
  <path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393"/>
</svg>"""

FLOPPY_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-floppy" viewBox="0 0 16 16">
  <path d="M11 2H9v3h2z"/>
  <path d="M1.5 0h11.586a1.5 1.5 0 0 1 1.06.44l1.415 1.414A1.5 1.5 0 0 1 16 2.914V14.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 14.5v-13A1.5 1.5 0 0 1 1.5 0M1 1.5v13a.5.5 0 0 0 .5.5H2v-4.5A1.5 1.5 0 0 1 3.5 9h9a1.5 1.5 0 0 1 1.5 1.5V15h.5a.5.5 0 0 0 .5-.5V2.914a.5.5 0 0 0-.146-.353l-1.415-1.415A.5.5 0 0 0 13.086 1H13v4.5A1.5 1.5 0 0 1 11.5 7h-7A1.5 1.5 0 0 1 3 5.5V1H1.5a.5.5 0 0 0-.5.5m3 4a.5.5 0 0 0 .5.5h7a.5.5 0 0 0 .5-.5V1H4zM3 15h10v-4.5a.5.5 0 0 0-.5-.5h-9a.5.5 0 0 0-.5.5z"/>
</svg>"""

def icon_from_colored_svg(svg_text: str, color: str) -> QIcon:
    colored_svg = svg_text.replace('fill="currentColor"', f'fill="{color}"')
    pixmap = QPixmap()
    pixmap.loadFromData(colored_svg.encode("utf-8"), "SVG")
    return QIcon(pixmap)


def pixmap_from_colored_svg(svg_text: str, color: str, size: int) -> QPixmap:
    colored_svg = svg_text.replace('fill="currentColor"', f'fill="{color}"')
    pixmap = QPixmap()
    pixmap.loadFromData(colored_svg.encode("utf-8"), "SVG")
    return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AccuTester")
        self.resize(600, 650)
        self.setObjectName("root")

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        self.page_segment = QFrame()
        self.page_segment.setObjectName("pageSegment")
        self.page_segment.setFixedHeight(44)

        page_row = QHBoxLayout(self.page_segment)
        page_row.setContentsMargins(4, 4, 4, 4)
        page_row.setSpacing(4)

        self.btn_page_temp = QPushButton("Temperatuur meting")
        self.btn_page_temp.setObjectName("pageButton")
        self.btn_page_temp.setProperty("active", True)
        self.btn_page_temp.setIconSize(QSize(14, 14))

        self.btn_page_graph = QPushButton("Grafiek maken")
        self.btn_page_graph.setObjectName("pageButton")
        self.btn_page_graph.setProperty("active", False)
        self.btn_page_graph.setIconSize(QSize(14, 14))

        page_row.addWidget(self.btn_page_temp)
        page_row.addWidget(self.btn_page_graph)
        root.addWidget(self.page_segment)

        self.status_card = QFrame()
        self.status_card.setObjectName("statusCard")
        self.status_card.setFixedHeight(44)

        status_card_layout = QHBoxLayout(self.status_card)
        status_card_layout.setContentsMargins(14, 0, 14, 0)
        status_card_layout.setSpacing(10)

        self.status = QLabel("Opstarten: Arduino zoeken...")
        self.status.setObjectName("status")
        self.status.setWordWrap(False)
        self.status.setMinimumWidth(0)
        self.status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self.status_connection_divider = QFrame()
        self.status_connection_divider.setObjectName("connectionDivider")
        self.status_connection_divider.setFixedWidth(1)
        self.status_connection_divider.setFixedHeight(24)

        self.conn_dot = QFrame()
        self.conn_dot.setObjectName("connDot")
        self.conn_dot.setProperty("state", "searching")
        self.conn_dot.setFixedSize(10, 10)

        self.connection_state_label = QLabel("Verbinden")
        self.connection_state_label.setObjectName("connectionStateText")
        self.connection_state_label.setProperty("state", "searching")

        self.connection_divider = QFrame()
        self.connection_divider.setObjectName("connectionDivider")
        self.connection_divider.setFixedWidth(1)
        self.connection_divider.setFixedHeight(22)

        self.lbl_port = QLabel("Poort:")
        self.lbl_port.setObjectName("portLabel")

        self.port_combo = ArrowComboBox()
        self.port_combo.setObjectName("portCombo")
        self.port_combo.setFixedWidth(120)
        self.port_combo.currentIndexChanged.connect(self.on_port_selected)

        status_card_layout.addWidget(self.status, 1)
        status_card_layout.addWidget(self.status_connection_divider)
        status_card_layout.addWidget(self.conn_dot)
        status_card_layout.addWidget(self.connection_state_label)
        status_card_layout.addWidget(self.connection_divider)
        status_card_layout.addWidget(self.lbl_port)
        status_card_layout.addWidget(self.port_combo)
        root.addWidget(self.status_card)

        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

        self.temp_page = QWidget()
        temp_root = QVBoxLayout(self.temp_page)
        temp_root.setContentsMargins(0, 0, 0, 0)
        temp_root.setSpacing(6)

        self.graph_page = QWidget()
        graph_root = QVBoxLayout(self.graph_page)
        graph_root.setContentsMargins(0, 0, 0, 0)
        graph_root.setSpacing(6)

        graph_card = QFrame()
        graph_card.setObjectName("card")
        graph_layout = QVBoxLayout(graph_card)
        graph_layout.setContentsMargins(18, 16, 18, 18)
        graph_layout.setSpacing(16)

        graph_title_row = QHBoxLayout()
        graph_title_row.setSpacing(8)

        graph_title_texts = QVBoxLayout()
        graph_title_texts.setSpacing(2)

        graph_title = QLabel("Selecteer bestanden")
        graph_title.setObjectName("graphSectionTitle")

        graph_title_texts.addWidget(graph_title)
        graph_title_row.addLayout(graph_title_texts)
        graph_title_row.addStretch(1)
        graph_layout.addLayout(graph_title_row)

        self.graph_selected_file_1 = ""
        self.graph_selected_file_2 = ""

        self.btn_select_graph_file_1 = FileDropButton(
            FILE_ICON_SVG,
            "Temperatuurmeting folder",
            select_mode="folder",
            icon_size=92,
            hint_text="Sleep hier de temperatuurmetingen map\nof klik om te selecteren",
            placeholder_text="Geen folder geselecteerd"
        )
        self.btn_select_graph_file_1.setMinimumHeight(275)
        self.btn_select_graph_file_1.file_selected_callback = lambda path: self.set_graph_file(1, path)

        self.btn_select_graph_file_2 = FileDropButton(
            LIGHTNING_ICON_SVG,
            "Elektriciteitsmetingen",
            select_mode="file",
            icon_size=98,
            hint_text="Sleep hier het elektriciteitsbestand\nof klik om te selecteren",
            placeholder_text="Geen bestand geselecteerd"
        )
        self.btn_select_graph_file_2.setMinimumHeight(275)
        self.btn_select_graph_file_2.file_selected_callback = lambda path: self.set_graph_file(2, path)

        file_select_row = QHBoxLayout()
        file_select_row.setSpacing(18)
        file_select_row.addWidget(self.btn_select_graph_file_1, 1)
        file_select_row.addWidget(self.btn_select_graph_file_2, 1)

        graph_layout.addLayout(file_select_row)
        graph_root.addWidget(graph_card, alignment=Qt.AlignTop)

        self.graph_output_dir = ""

        self.graph_action_card = QFrame()
        self.graph_action_card.setObjectName("card")
        graph_action_layout = QHBoxLayout(self.graph_action_card)
        graph_action_layout.setContentsMargins(18, 14, 18, 14)
        graph_action_layout.setSpacing(16)

        graph_action_left = QVBoxLayout()
        graph_action_left.setSpacing(9)

        self.graph_action_title = QLabel("Grafiek maken")
        self.graph_action_title.setObjectName("graphSectionTitle")

        self.input_graph_title = QLineEdit()
        self.input_graph_title.setPlaceholderText("Titel grafiek")
        self.input_graph_title.setText("")

        graph_location_row = QHBoxLayout()
        graph_location_row.setSpacing(10)

        self.lbl_graph_output_path = QLabel("Geen opslaglocatie geselecteerd")
        self.lbl_graph_output_path.setObjectName("graphOutputPath")
        self.lbl_graph_output_path.setMinimumWidth(0)
        self.lbl_graph_output_path.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self.btn_graph_browse = QPushButton("Bladeren")
        self.btn_graph_browse.setObjectName("graphBrowseButton")
        self.btn_graph_browse.setFixedWidth(110)

        graph_location_row.addWidget(self.lbl_graph_output_path, 1)
        graph_location_row.addWidget(self.btn_graph_browse)

        graph_action_left.addWidget(self.graph_action_title)
        graph_action_left.addWidget(self.input_graph_title)
        graph_action_left.addLayout(graph_location_row)

        graph_action_separator = QFrame()
        graph_action_separator.setObjectName("connectionDivider")
        graph_action_separator.setFixedWidth(1)

        self.btn_make_graph = QPushButton("Maak grafiek")
        self.btn_make_graph.setObjectName("makeGraphButton")
        self.btn_make_graph.setIcon(icon_from_colored_svg(PAGE_GRAPH_ICON_SVG, "#ffffff"))
        self.btn_make_graph.setIconSize(QSize(20, 20))
        self.btn_make_graph.setMinimumSize(190, 72)
        self.btn_make_graph.setEnabled(False)

        graph_action_layout.addLayout(graph_action_left, 1)
        graph_action_layout.addWidget(graph_action_separator)
        graph_action_layout.addWidget(self.btn_make_graph)

        graph_root.addWidget(self.graph_action_card)
        graph_root.addStretch(1)

        self.pages.addWidget(self.temp_page)
        self.pages.addWidget(self.graph_page)
        self.pages.setCurrentWidget(self.temp_page)

        self.btn_page_temp.clicked.connect(lambda: self.switch_page(0))
        self.btn_page_graph.clicked.connect(lambda: self.switch_page(1))
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        temp_root.addLayout(grid, 1)

        self.p1 = SensorPlot("Sensor 1")
        self.p2 = SensorPlot("Sensor 2")
        self.p3 = SensorPlot("Sensor 3")
        self.p4 = SensorPlot("Sensor 4")

        grid.addWidget(self.p1, 0, 0)
        grid.addWidget(self.p2, 0, 1)
        grid.addWidget(self.p3, 1, 0)
        grid.addWidget(self.p4, 1, 1)

        self.env_card = QFrame()
        self.env_card.setObjectName("card")
        temp_root.addWidget(self.env_card)

        env_outer = QHBoxLayout(self.env_card)
        env_outer.setContentsMargins(14, 12, 14, 12)
        env_outer.setSpacing(14)

        env_left = QVBoxLayout()
        env_left.setSpacing(8)

        settings_title_row = QHBoxLayout()
        settings_title_row.setSpacing(7)

        self.settings_title = QLabel("Test instellingen")
        self.settings_title.setObjectName("sectionTitle")
        self.settings_title.setStyleSheet("font-weight: 800;")

        settings_title_row.addWidget(self.settings_title)
        settings_title_row.addStretch(1)
        env_left.addLayout(settings_title_row)

        sensor_grid = QGridLayout()
        sensor_grid.setHorizontalSpacing(12)
        sensor_grid.setVerticalSpacing(7)

        self.loc_sensor1 = QLineEdit()
        self.loc_sensor2 = QLineEdit()
        self.loc_sensor3 = QLineEdit()
        self.loc_sensor4 = QLineEdit()

        sensor_inputs = [
            ("Sensor 1:", self.loc_sensor1),
            ("Sensor 2:", self.loc_sensor2),
            ("Sensor 3:", self.loc_sensor3),
            ("Sensor 4:", self.loc_sensor4),
        ]

        for i, (label_text, line_edit) in enumerate(sensor_inputs):
            row = i // 2
            col = (i % 2) * 2

            label = QLabel(label_text)
            label.setObjectName("settingsLabel")
            line_edit.setPlaceholderText("Plaatsing")
            line_edit.setFixedWidth(120)
            line_edit.setFixedHeight(28)

            sensor_grid.addWidget(label, row, col)
            sensor_grid.addWidget(line_edit, row, col + 1)

        env_left.addLayout(sensor_grid)

        env_grid = QGridLayout()
        env_grid.setHorizontalSpacing(12)
        env_grid.setVerticalSpacing(7)

        self.lbl_env = QLabel("Omgevingstemperatuur:")
        self.lbl_env.setObjectName("settingsLabel")
        self.input_env_temp = QLineEdit()
        self.input_env_temp.setPlaceholderText("0.0")
        self.input_env_temp.setFixedWidth(80)
        self.input_env_temp.setFixedHeight(28)
        self.input_env_temp.setMaxLength(8)
        env_validator = QDoubleValidator(-100.0, 1000.0, 2, self)
        env_validator.setNotation(QDoubleValidator.StandardNotation)
        self.input_env_temp.setValidator(env_validator)
        self.lbl_env_unit = QLabel("°C")
        self.lbl_env_unit.setObjectName("settingsLabel")
        self.btn_log_env_temp = QPushButton("Loggen")
        self.btn_log_env_temp.setObjectName("mainButton")
        self.btn_log_env_temp.setIcon(icon_from_colored_svg(FLOPPY_ICON_SVG, "#6b7280"))
        self.btn_log_env_temp.setIconSize(QSize(14, 14))
        self.btn_log_env_temp.setFixedSize(104, 32)
        self.btn_log_env_temp.setEnabled(False)

        env_grid.addWidget(self.lbl_env, 0, 0)
        env_grid.addWidget(self.input_env_temp, 0, 1)
        env_grid.addWidget(self.lbl_env_unit, 0, 2)
        env_grid.addWidget(self.btn_log_env_temp, 0, 3)
        env_left.addLayout(env_grid)

        env_outer.addStretch(1)
        env_outer.addLayout(env_left, 0)
        env_outer.addStretch(1)

        self.log_card = QFrame()
        self.log_card.setObjectName("card")
        temp_root.addWidget(self.log_card)

        log_card_layout = QHBoxLayout(self.log_card)
        log_card_layout.setContentsMargins(14, 10, 14, 10)
        log_card_layout.setSpacing(10)

        self.btn_browse = BrowseButton("Bladeren")
        self.btn_browse.setObjectName("mainButton")
        self.btn_toggle_log = QPushButton("Loggen starten")
        self.btn_toggle_log.setObjectName("logButton")
        self.btn_toggle_log.setProperty("mode", "start")
        self.btn_toggle_log.setEnabled(False)

        log_card_layout.addWidget(self.btn_browse)
        log_card_layout.addWidget(self.btn_toggle_log)

        self.last_plot_update = 0
        self.latest_temps = [None, None, None, None]

        self.ser = None
        self.connected_port = ""
        self.logging_enabled = False
        self.test_status = "uit"
        self.log_base_dir = ""
        self.current_log_folder = ""
        self.current_log_path = ""
        self.log_file = None
        self.log_writer = None
        self.retry_reason = "Arduino niet gevonden."
        self.retry_state = "searching"
        self.retry_seconds_left = RECONNECT_INTERVAL_S

        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.setInterval(1000)
        self.reconnect_timer.timeout.connect(self._reconnect_tick)

        self.available_ports = []
        self.manual_port_change_enabled = False

        self.btn_browse.clicked.connect(self.choose_log_path)
        self.btn_toggle_log.clicked.connect(self.toggle_logging)
        self.btn_log_env_temp.clicked.connect(self.log_environment_temperature)
        self.btn_graph_browse.clicked.connect(self.choose_graph_output_path)
        self.btn_make_graph.clicked.connect(self.make_graph)

        self.refresh_port_list()
        self.connect_serial(show_retry_message=True)

        self.timer = QTimer(self)
        self.timer.setInterval(int(1000 / SAMPLE_HZ))
        self.timer.timeout.connect(self.poll_serial)
        self.timer.start()


    def update_make_graph_button_state(self):
        valid = (
            bool(self.graph_selected_file_1) and
            bool(self.graph_selected_file_2) and
            bool(self.graph_output_dir)
        )
        self.btn_make_graph.setEnabled(valid)

    def choose_graph_output_path(self):
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Kies opslaglocatie voor grafiek",
            default_dir
        )
        if not folder:
            return

        self.graph_output_dir = folder
        self.lbl_graph_output_path.setText(self.graph_output_dir)
        self.lbl_graph_output_path.setToolTip(self.graph_output_dir)
        self.status.setText(f"Grafiek opslaglocatie gekozen: {self.graph_output_dir}")
        self.update_make_graph_button_state()

    def make_graph(self):
        if not self.graph_selected_file_1:
            self.status.setText("Kies eerst een temperatuurmeting folder")
            return
        if not self.graph_selected_file_2:
            self.status.setText("Kies eerst een elektriciteitsmeting bestand")
            return
        if not self.graph_output_dir:
            self.status.setText("Kies eerst een opslaglocatie met Bladeren")
            return

        self.btn_make_graph.setEnabled(False)
        self.status.setText("Grafiek wordt gemaakt...")

        try:
            # Lazy import graph_maker only when needed (for faster startup)
            from graph_maker import make_graph_from_files
            
            graph_title = self.input_graph_title.text().strip() or "Temperatuur spanning test"
            result = make_graph_from_files(
                temperature_folder=Path(self.graph_selected_file_1),
                voltage_file=Path(self.graph_selected_file_2),
                output_base_dir=Path(self.graph_output_dir),
                title=graph_title,
            )
            self.status.setText(f"Grafiek gemaakt: {result.graph_path}")
        except Exception as e:
            self.status.setText(f"Grafiek maken mislukt: {e}")
        finally:
            self.update_make_graph_button_state()

    def set_graph_file(self, file_number: int, file_path: str):
        file_name = os.path.basename(file_path.rstrip(os.sep))

        if file_number == 1:
            self.graph_selected_file_1 = file_path
            self.btn_select_graph_file_1.set_selected_display_text(file_name)
            self.btn_select_graph_file_1.setToolTip(file_path)
        else:
            self.graph_selected_file_2 = file_path
            self.btn_select_graph_file_2.set_selected_display_text(file_name)
            self.btn_select_graph_file_2.setToolTip(file_path)

        self.update_make_graph_button_state()

    def switch_page(self, index: int):
        self.pages.setCurrentIndex(index)
        self.btn_page_temp.setProperty("active", index == 0)
        self.btn_page_graph.setProperty("active", index == 1)
        self._update_page_button_icons()
        self._update_status_card_for_page(index)

        for btn in (self.btn_page_temp, self.btn_page_graph):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _update_page_button_icons(self):
        temp_color = "#ffffff" if self.btn_page_temp.property("active") else "#374151"
        graph_color = "#ffffff" if self.btn_page_graph.property("active") else "#374151"
        self.btn_page_temp.setIcon(icon_from_colored_svg(PAGE_TEMP_ICON_SVG, temp_color))
        self.btn_page_graph.setIcon(icon_from_colored_svg(PAGE_GRAPH_ICON_SVG, graph_color))

    def _update_status_card_for_page(self, index: int):
        show_connection = index == 0
        for widget in (
            self.status_connection_divider,
            self.conn_dot,
            self.connection_state_label,
            self.connection_divider,
            self.lbl_port,
            self.port_combo,
        ):
            widget.setVisible(show_connection)

    def _refresh_status_style(self):
        for widget in (self.conn_dot, self.connection_state_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _set_connection_state(self, state: str, text: str):
        self.conn_dot.setProperty("state", state)
        self.connection_state_label.setProperty("state", state)
        if state == "connected":
            self.connection_state_label.setText("Actief")
        elif state == "searching":
            self.connection_state_label.setText("Verbinden")
        else:
            self.connection_state_label.setText("Verbroken")
        self._refresh_status_style()
        self.status.setText(text)

    def _start_reconnect_loop(self, reason: str, state: str):
        self.retry_reason = reason
        self.retry_state = state
        self.retry_seconds_left = RECONNECT_INTERVAL_S
        self._set_connection_state(
            state,
            f"{reason} Opnieuw proberen over {self.retry_seconds_left}s..."
        )
        if not self.reconnect_timer.isActive():
            self.reconnect_timer.start()

    def _stop_reconnect_loop(self):
        if self.reconnect_timer.isActive():
            self.reconnect_timer.stop()
        self.retry_seconds_left = RECONNECT_INTERVAL_S
    
    def _reconnect_tick(self):
        if self.ser and self.ser.is_open:
            self._stop_reconnect_loop()
            return

        self.refresh_port_list()

        self.retry_seconds_left -= 1
        if self.retry_seconds_left <= 0:
            if self.connect_serial(show_retry_message=False):
                return
            self.retry_seconds_left = RECONNECT_INTERVAL_S

        self._set_connection_state(
            self.retry_state,
            f"{self.retry_reason} Opnieuw proberen over {self.retry_seconds_left}s..."
        )

    def _update_log_button_state(self):
        can_start = bool(self.log_base_dir and self.ser and self.ser.is_open and not self.logging_enabled)
        can_stop = bool(self.logging_enabled)
        self.btn_toggle_log.setEnabled(can_start or can_stop)
        has_log_dir = bool(self.log_base_dir)
        self.btn_log_env_temp.setEnabled(has_log_dir)
        
    def refresh_port_list(self, selected_port: str = ""):
        ports = list_serial_ports()
        self.available_ports = ports[:]

        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        self.port_combo.addItem("Kies COM")

        for port in ports:
            self.port_combo.addItem(port)

        target = selected_port or self.connected_port
        if target and target in ports:
            self.port_combo.setCurrentText(target)
        else:
            self.port_combo.setCurrentIndex(0)

        self.port_combo.blockSignals(False)
        self.manual_port_change_enabled = True


    def on_port_selected(self, index: int):
        if not self.manual_port_change_enabled:
            return

        if index <= 0:
            return

        port = self.port_combo.currentText().strip()
        if not port:
            return

        if self.ser and self.ser.is_open and port == self.connected_port:
            self.status.setText(f"Al verbonden met {port}")
            return

        self.status.setText(f"Handmatig verbinden met {port}...")
        self.connect_serial(selected_port=port, show_retry_message=True, manual=True)

    def _ensure_session_folder(self):
        if self.current_log_folder:
            return self.current_log_folder
        if not self.log_base_dir:
            return ""
        self.current_log_folder = self._make_session_folder()
        return self.current_log_folder

    def _get_env_log_path(self):
        if not self.current_log_folder:
            return ""
        return os.path.join(self.current_log_folder, "testcondities.csv")

    def log_environment_temperature(self):
        if not self.log_base_dir:
            self.status.setText("Kies eerst een logmap voor omgevingstemperatuur")
            return

        raw = self.input_env_temp.text().strip().replace(",", ".")
        if not raw:
            self.status.setText("Vul een omgevingstemperatuur in")
            return

        try:
            env_temp = float(raw)
        except ValueError:
            self.status.setText("Omgevingstemperatuur moet een getal zijn")
            return

        if self._write_test_condition_row(f"{env_temp:.2f}"):
            self.input_env_temp.clear()
            self.status.setText(f"Omgevingstemperatuur gelogd: {env_temp:.2f}°C")

    def _write_test_condition_row(self, env_temp: str = ""):
        if not self.log_base_dir:
            self.status.setText("Kies eerst een logmap")
            return False

        try:
            self._ensure_session_folder()
        except Exception as e:
            self.status.setText(f"Kan logmap niet maken: {e}")
            return False

        env_log_path = self._get_env_log_path()
        if not env_log_path:
            self.status.setText("Geen logmap beschikbaar voor testcondities")
            return False

        try:
            is_new_file = not os.path.exists(env_log_path) or os.path.getsize(env_log_path) == 0
            with open(env_log_path, "a", newline="", encoding="utf-8") as env_file:
                writer = csv.writer(env_file)
                if is_new_file:
                    writer.writerow([
                        "timestamp",
                        "omgevingstemp",
                        "status",
                        "locsensor1",
                        "locsensor2",
                        "locsensor3",
                        "locsensor4"
                    ])

                ts = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                writer.writerow([
                    ts,
                    env_temp,
                    self.test_status,
                    self.loc_sensor1.text().strip(),
                    self.loc_sensor2.text().strip(),
                    self.loc_sensor3.text().strip(),
                    self.loc_sensor4.text().strip()
                ])
            return True
        except Exception as e:
            self.status.setText(f"Schrijffout testcondities: {e}")
            return False



    def _close_serial(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None
        self.connected_port = ""

    def _handle_disconnect(self, reason: str):
        self._close_serial()

        for p in (self.p1, self.p2, self.p3, self.p4):
            p.mark_gap()

        if self.logging_enabled:
            self.stop_logging(status_text=f"{reason} - logging gestopt")

        self.refresh_port_list()
        self._start_reconnect_loop(reason, "retrying")
        self._update_log_button_state()

    def choose_log_path(self):
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Kies loglocatie",
            default_dir
        )
        if not folder:
            return

        self.log_base_dir = folder
        short_text = self.log_base_dir[:25]
        self.btn_browse.set_selected_text(short_text)
        self._update_log_button_state()
        self.status.setText(f"Loglocatie gekozen: {self.log_base_dir}")

    def _make_session_folder(self):
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = os.path.join(self.log_base_dir, f"Temperatuur_meting_{ts}")
        os.makedirs(folder, exist_ok=False)
        return folder

    def start_logging(self):
        if not self.log_base_dir:
            return False
        if not (self.ser and self.ser.is_open):
            self.status.setText("Niet verbonden met Arduino: logging niet gestart")
            return False

        try:
            folder = self._ensure_session_folder()
            if not folder:
                self.status.setText("Geen logmap beschikbaar")
                return False
            self.current_log_path = os.path.join(self.current_log_folder, "metingen.csv")

            self.log_file = open(self.current_log_path, "w", newline="", encoding="utf-8")
            self.log_writer = csv.writer(self.log_file)
            self.log_writer.writerow(["timestamp", "sensor1", "sensor2", "sensor3", "sensor4"])
            self.log_file.flush()

            self.logging_enabled = True
            self.btn_toggle_log.setText("Loggen stoppen")
            self.btn_toggle_log.setProperty("mode", "stop")
            self.btn_toggle_log.style().unpolish(self.btn_toggle_log)
            self.btn_toggle_log.style().polish(self.btn_toggle_log)
            self.btn_browse.setEnabled(False)
            self._update_log_button_state()
            self.status.setText(f"Logging actief: {self.current_log_folder}")
            return True
        except Exception as e:
            self.logging_enabled = False
            self.log_file = None
            self.log_writer = None
            self.current_log_folder = ""
            self.current_log_path = ""
            self.status.setText(f"Kan logbestand niet openen: {e}")
            return False

    def stop_logging(self, status_text: str = "Logging gestopt"):
        self.logging_enabled = False
        self.log_writer = None
        try:
            if self.log_file:
                self.log_file.close()
        except Exception:
            pass
        self.log_file = None
        self.current_log_folder = ""
        self.current_log_path = ""

        self.btn_toggle_log.setText("Loggen starten")
        self.btn_toggle_log.setProperty("mode", "start")
        self.btn_toggle_log.style().unpolish(self.btn_toggle_log)
        self.btn_toggle_log.style().polish(self.btn_toggle_log)
        self.btn_browse.setEnabled(True)
        self._update_log_button_state()
        self.status.setText(status_text)

    def toggle_logging(self):
        if self.logging_enabled:
            self.stop_logging()
        else:
            self.start_logging()
    
    def connect_serial(self, selected_port: str = "", show_retry_message: bool = True, manual: bool = False):
        if self.ser and self.ser.is_open:
            if selected_port and selected_port != self.connected_port:
                self._close_serial()
            else:
                self.refresh_port_list(selected_port=self.connected_port)
                return True

        self.refresh_port_list(selected_port=selected_port)

        port = selected_port if selected_port else find_arduino_port()

        if not port:
            ports = [p.device for p in list_ports.comports()]
            port_list = ", ".join(ports) if ports else "geen beschikbare COM-poorten"
            self.retry_reason = f"Arduino niet gevonden ({port_list})."
            self.retry_state = "searching"
            if show_retry_message:
                self._start_reconnect_loop(self.retry_reason, self.retry_state)
            self._update_log_button_state()
            self.refresh_port_list()
            return False

        try:
            self.ser = serial.Serial(port, BAUD, timeout=0.02)
            self.connected_port = port
            if manual:
                self._set_connection_state("connected", f"Handmatig verbonden: {port} @ {BAUD}")
            else:
                self._set_connection_state("connected", f"Verbonden: {port} @ {BAUD}")
            self._update_log_button_state()
            self._stop_reconnect_loop()
            self.refresh_port_list(selected_port=port)
            return True
        except Exception as e:
            self._close_serial()
            if manual:
                self.retry_reason = f"Kan handmatig gekozen poort {port} niet openen ({e})."
            else:
                self.retry_reason = f"Kan {port} niet openen ({e})."
            self.retry_state = "searching"
            if show_retry_message:
                self._start_reconnect_loop(self.retry_reason, self.retry_state)
            self._update_log_button_state()
            self.refresh_port_list(selected_port=port)
            return False

    def _update_shared_y_axis(self):
        ys = []
        for p in (self.p1, self.p2, self.p3, self.p4):
            if len(p.y) > 0:
                ys.extend([v for v in p.y if not math.isnan(v)])

        if len(ys) < 5:
            return

        ymin = min(ys)
        ymax = max(ys)

        margin = max(0.3, 0.15 * (ymax - ymin))
        if ymin == ymax:
            ymin -= 0.5
            ymax += 0.5
        else:
            ymin -= margin
            ymax += margin

        span = ymax - ymin
        if span < MIN_Y_SPAN:
            center = (ymin + ymax) / 2.0
            half = MIN_Y_SPAN / 2.0
            ymin = center - half
            ymax = center + half

        for p in (self.p1, self.p2, self.p3, self.p4):
            p.set_shared_y_range(ymin, ymax)

    def poll_serial(self):
        if not self.ser:
            return

        if not self.ser.is_open:
            self._handle_disconnect("Arduino verbinding verbroken.")
            return

        try:
            line = self.ser.readline().decode(errors="ignore").strip()
            if not line.startswith("T,"):
                return

            parts = line.split(",")
            if len(parts) != 5:
                return

            temps = []
            for v in parts[1:]:
                try:
                    temps.append(float(v))
                except:
                    temps.append(None)
            
            self.latest_temps = temps

            now = time.time()
            if now - self.last_plot_update >= PLOT_UPDATE_INTERVAL_S:
                if temps[0] is not None: self.p1.add_point(temps[0])
                if temps[1] is not None: self.p2.add_point(temps[1])
                if temps[2] is not None: self.p3.add_point(temps[2])
                if temps[3] is not None: self.p4.add_point(temps[3])

                self._update_shared_y_axis()
                self.last_plot_update = now

            if self.logging_enabled and self.log_writer and self.log_file:
                try:
                    ts = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    row = [ts, parts[1], parts[2], parts[3], parts[4]]
                    self.log_writer.writerow(row)
                except Exception as e:
                    self.stop_logging()
                    self.status.setText(f"Schrijffout, logging gestopt: {e}")


        except (serial.SerialException, OSError):
            self._handle_disconnect("Arduino losgekoppeld of COM-fout.")
        except Exception:
            pass

    def closeEvent(self, event):
        self.stop_logging()
        self._stop_reconnect_loop()
        self._close_serial()
        super().closeEvent(event)
