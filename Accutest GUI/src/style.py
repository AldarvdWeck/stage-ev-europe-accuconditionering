from PySide6.QtWidgets import QApplication
import pyqtgraph as pg
from config import APP_BG, CARD_BG, BORDER, TEXT, SUBTEXT

def apply_style(app: QApplication):
    app.setStyleSheet(f"""
    QWidget#root {{
        background: {APP_BG};
    }}
    QLabel {{
        color: {TEXT};
        font-size: 12px;
    }}
    QFrame#pageSegment {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
    }}
    QFrame#statusCard {{
        background: #ffffff;
        border: 1px solid {BORDER};
        border-radius: 12px;
    }}
    QLabel#status {{
        color: {SUBTEXT};
        font-size: 12px;
        padding: 0px 2px;
    }}
    QFrame#connDot {{
        border-radius: 5px;
        border: 1px solid #9ca3af;
        background: #9ca3af;
    }}
    QFrame#connDot[state="connected"] {{
        border: 1px solid #16a34a;
        background: #16a34a;
    }}
    QFrame#connDot[state="searching"] {{
        border: 1px solid #f59e0b;
        background: #f59e0b;
    }}
    QFrame#connDot[state="retrying"] {{
        border: 1px solid #ef4444;
        background: #ef4444;
    }}
    QLabel#connectionStateText {{
        color: #6b7280;
        font-size: 12px;
        font-weight: 700;
    }}
    QLabel#connectionStateText[state="connected"] {{
        color: #15803d;
    }}
    QLabel#connectionStateText[state="searching"] {{
        color: #d97706;
    }}
    QLabel#connectionStateText[state="retrying"] {{
        color: #dc2626;
    }}
    QFrame#connectionDivider {{
        background: #e5e7eb;
        border: none;
    }}
    QLabel#portLabel {{
        color: #6b7280;
        font-size: 12px;
        font-weight: 500;
    }}
    QFrame#card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 12px;
    }}
    QLabel#cardTitle {{
        color: {SUBTEXT};
        font-size: 12px;
    }}
    QLabel#cardValue {{
        color: {TEXT};
        font-size: 18px;
        font-weight: 600;
    }}
    QPushButton#pageButton {{
        background: transparent;
        color: #374151;
        border: none;
        border-radius: 9px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 700;
        text-align: center;
    }}
    QPushButton#pageButton:hover {{
        background: #f8fafc;
    }}
    QPushButton#pageButton[active="true"] {{
        background: #16a34a;
        color: #ffffff;
    }}
    QPushButton#pageButton[active="true"]:hover {{
        background: #15803d;
    }}
    QPushButton#fileDropButton {{
        background: #ffffff;
        color: #4b5563;
        border: 2px dashed #cbd5e1;
        border-radius: 18px;
        font-size: 13px;
        font-weight: 700;
        padding: 12px;
        min-height: 220px;
    }}
    QPushButton#fileDropButton:hover {{
        background: #f8fafc;
        border: 2px dashed #16a34a;
        color: #111827;
    }}
    QPushButton#fileDropButton[dragging="true"] {{
        background: #f0fdf4;
        border: 2px dashed #16a34a;
        color: #15803d;
    }}
    QLabel#fileTypeText {{
        color: #111827;
        font-size: 12px;
        font-weight: 700;
    }}
    QLabel#selectedFileText {{
        color: #4b5563;
        font-size: 12px;
        font-weight: 500;
    }}

    QLabel#graphSectionIcon {{
        color: #16a34a;
        font-size: 15px;
        font-weight: 700;
    }}
    QLabel#graphSectionTitle {{
        color: #111827;
        font-size: 14px;
        font-weight: 800;
    }}
    QLabel#graphSectionSubtitle {{
        color: #6b7280;
        font-size: 12px;
        font-weight: 500;
    }}
    QLabel#fileDropButtonTitle {{
        color: #111827;
        font-size: 13px;
        font-weight: 800;
    }}
    QLabel#fileDropButtonHint {{
        color: #6b7280;
        font-size: 11px;
        font-weight: 500;
    }}
    QFrame#fileSelectedChip {{
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
    }}
    QLabel#fileSelectedText {{
        color: #4b5563;
        font-size: 11px;
        font-weight: 600;
    }}

    QFrame#fileSelectedChip[selected="true"] {{
        background: #ecfdf5;
        border: 1px solid #bbf7d0;
    }}
    QLabel#fileSelectedText[selected="true"] {{
        color: #15803d;
        font-weight: 700;
    }}
    QPushButton#fileDropButton[selected="true"] {{
        background: #f0fdf4;
        border: 2px dashed #16a34a;
        color: #15803d;
    }}
    QPushButton#fileDropButton[selected="true"] QLabel#fileDropButtonTitle {{
        color: #15803d;
    }}
    QPushButton#mainButton {{
        background: #e5e7eb;
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton#mainButton:hover {{
        background: #dbe1e8;
    }}
    QPushButton#mainButton:disabled {{
        color: #9ca3af;
        background: #f3f4f6;
    }}
    QPushButton#syncButton {{
        color: #ffffff;
        border: 1px solid transparent;
        border-radius: 14px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 700;
        text-align: left;
    }}
    QPushButton#syncButton[state="start"] {{
        background: #16a34a;
    }}
    QPushButton#syncButton[state="start"]:hover {{
        background: #15803d;
    }}
    QPushButton#syncButton[state="stop"] {{
        background: #dc2626;
    }}
    QPushButton#syncButton[state="stop"]:hover {{
        background: #b91c1c;
    }}
    QPushButton#syncButton:disabled {{
        color: #d1d5db;
        background: #9ca3af;
    }}
    QPushButton#syncButton:disabled QLabel#syncButtonTitle {{
        color: #f9fafb;
    }}
    QPushButton#syncButton:disabled QLabel#syncButtonSubtitle {{
        color: #e5e7eb;
    }}
    QPushButton#logButton {{
        color: #ffffff;
        border: 1px solid transparent;
        border-radius: 12px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 700;
    }}
    QPushButton#logButton[mode="start"] {{
        background: #16a34a;
    }}
    QPushButton#logButton[mode="start"]:hover {{
        background: #15803d;
    }}
    QPushButton#logButton[mode="stop"] {{
        background: #dc2626;
    }}
    QPushButton#logButton[mode="stop"]:hover {{
        background: #b91c1c;
    }}
    QPushButton#logButton:disabled {{
        color: #d1d5db;
        background: #9ca3af;
    }}


    QLabel#graphOutputPath {{
        background: #ffffff;
        color: #111827;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 9px 12px;
        font-size: 12px;
        font-weight: 500;
    }}
    QPushButton#graphBrowseButton {{
        background: #e5e7eb;
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 700;
    }}
    QPushButton#graphBrowseButton:hover {{
        background: #dbe1e8;
    }}
    QPushButton#makeGraphButton {{
        background: #16a34a;
        color: #ffffff;
        border: 1px solid transparent;
        border-radius: 14px;
        padding: 10px 18px;
        font-size: 17px;
        font-weight: 800;
    }}
    QPushButton#makeGraphButton:hover {{
        background: #15803d;
    }}
    QPushButton#makeGraphButton:disabled {{
        color: #d1d5db;
        background: #9ca3af;
    }}

    QLineEdit {{
        background: #ffffff;
        color: #111827;
        border: 1px solid #e5e7eb;
        border-radius: 7px;
        padding: 4px 8px;
        font-size: 11px;
    }}
    QLineEdit:focus {{
        border: 1px solid #16a34a;
    }}
    QComboBox#portCombo {{
        background: #ffffff;
        color: #111827;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 5px 24px 5px 10px;
        font-size: 12px;
        font-weight: 600;
        min-height: 18px;
    }}
    QComboBox#portCombo:hover {{
        background: #ffffff;
        border: 1px solid #d1d5db;
    }}
    QComboBox#portCombo::drop-down {{
        border: none;
        width: 22px;
        background: transparent;
    }}
    QComboBox#portCombo::down-arrow {{
        image: none;
        width: 0px;
        height: 0px;
    }}
    QComboBox#portCombo QAbstractItemView {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        font-size: 12px;
        border-radius: 8px;
        selection-background-color: #f3f4f6;
        color: #111827;
        padding: 4px;
    }}
    """)
    pg.setConfigOptions(antialias=True)
