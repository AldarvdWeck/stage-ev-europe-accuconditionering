import time
import math
from collections import deque

from PySide6.QtCore import QTimer, Qt, QEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout

from config import WINDOW_SECONDS, MAX_POINTS, MIN_Y_SPAN, LINE_COLOR, PLOT_BG, AXIS, BORDER

class SensorPlot(QFrame):
    def __init__(self, short_name: str):
        super().__init__()
        # Lazy import pyqtgraph for faster app startup
        import pyqtgraph as pg
        self._pg = pg
        
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        self.title = QLabel(short_name)
        self.title.setObjectName("cardTitle")

        self.value = QLabel("--.-°C")
        self.value.setObjectName("cardValue")
        self.value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header.addWidget(self.title)
        header.addStretch(1)
        header.addWidget(self.value)
        layout.addLayout(header)

        self.plot = self._pg.PlotWidget()
        layout.addWidget(self.plot)

        self.plot.setContentsMargins(0, 0, 0, 0)
        self.plot.getPlotItem().layout.setContentsMargins(0, 0, 0, 0)

        self.plot.setBackground(PLOT_BG)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(x=True, y=True, alpha=0.25)

        left = self.plot.getAxis("left")
        bottom = self.plot.getAxis("bottom")

        left.setTextPen(self._pg.mkPen(AXIS))
        bottom.setTextPen(self._pg.mkPen(AXIS))
        left.setPen(self._pg.mkPen(BORDER))
        bottom.setPen(self._pg.mkPen(BORDER))

        left.setWidth(30)
        bottom.setHeight(18)
        left.setStyle(tickTextOffset=4)
        bottom.setStyle(tickTextOffset=4)

        tick_font = self._pg.QtGui.QFont()
        tick_font.setPointSize(8)
        left.setTickFont(tick_font)
        bottom.setTickFont(tick_font)

        self.plot.getPlotItem().getViewBox().setBackgroundColor(PLOT_BG)

        fill_color = self._pg.mkColor(LINE_COLOR)
        fill_color.setAlpha(100)

        self.fill_bottom = self.plot.plot(pen=None)

        self.curve = self.plot.plot(pen=self._pg.mkPen(LINE_COLOR, width=2))

        self.fill = self._pg.FillBetweenItem(
            curve1=self.curve,
            curve2=self.fill_bottom,
            brush=self._pg.mkBrush(fill_color)
        )

        self.plot.addItem(self.fill)
        
        self.fill.setZValue(1)
        self.curve.setZValue(2)
        

        self.plot.setXRange(-WINDOW_SECONDS, 0, padding=0)

        self.y_axis_hint = QLabel("°C", self.plot)
        self.x_axis_hint = QLabel("s", self.plot)
        for hint in (self.y_axis_hint, self.x_axis_hint):
            hint.setStyleSheet(f"color: {AXIS}; font-size: 9px; font-weight: 600; background: transparent;")
            hint.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            hint.adjustSize()

        self.plot.installEventFilter(self)
        self._position_axis_hints()

        self.t0 = time.time()
        self.x = deque(maxlen=MAX_POINTS)
        self.y = deque(maxlen=MAX_POINTS)
        self.break_on_next_point = False

    def _position_axis_hints(self):
        left_w = int(self.plot.getAxis("left").width())
        bottom_h = int(self.plot.getAxis("bottom").height())

        self.y_axis_hint.adjustSize()
        self.x_axis_hint.adjustSize()

        y_x = 2
        y_y = 0
        self.y_axis_hint.move(y_x, y_y)

        x_x = max(left_w + 2, self.plot.width() - self.x_axis_hint.width() - 4)
        x_y = max(0, self.plot.height() - bottom_h + 1)
        self.x_axis_hint.move(x_x, x_y)

    def eventFilter(self, obj, event):
        if obj is self.plot and event.type() in (QEvent.Resize, QEvent.Show):
            QTimer.singleShot(0, self._position_axis_hints)
        return super().eventFilter(obj, event)

    def add_point(self, temp_c: float):
        now = time.time()
        age = now - self.t0

        if self.break_on_next_point and len(self.x) > 0:
            self.x.append(age - 1e-3)
            self.y.append(float("nan"))
            self.break_on_next_point = False

        self.x.append(age)
        self.y.append(temp_c)

        self.value.setText(f"{temp_c:0.1f}°C")

        x0 = self.x[-1]
        x_rel = [xi - x0 for xi in self.x]
        y_list = list(self.y)
        
        self.curve.setData(x_rel, y_list)

        valid_y = [v for v in y_list if not math.isnan(v)]
        if valid_y:
            baseline_y = self.plot.viewRange()[1][0]
        else:
            baseline_y = 0

        baseline = [baseline_y] * len(x_rel)

        self.fill_bottom.setData(x_rel, baseline)
        self.fill.setCurves(self.curve, self.fill_bottom)

        self.plot.setXRange(-WINDOW_SECONDS, 0, padding=0)

    def set_shared_y_range(self, ymin: float, ymax: float):
        self.plot.setYRange(ymin, ymax, padding=0)

    def mark_gap(self):
        self.break_on_next_point = True