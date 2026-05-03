import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPalette

from ui.theme import DARK, LIGHT, TRANSLATIONS
from tools.qrcode_tool import QRTool
from tools.translator_tool import TranslatorTool
from tools.weather_tool import WeatherTool
from tools.converter_tool import ConverterTool
from tools.file_converter_tool import FileConverterTool
from tools.calculator_tool import CalculatorTool
from tools.clock_tool import ClockTool
from tools.password_tool import PasswordTool
from tools.encoder_tool import EncoderTool
from tools.color_tool import ColorTool
from tools.metadata_tool import MetadataTool
from tools.media_tool import MediaTool
from tools.youtube_tool import YoutubeTool

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

TOOLS = [
    ("qr",        "🔲", QRTool),
    ("translator","🌍", TranslatorTool),
    ("weather",   "⛅", WeatherTool),
    ("converter", "⚖️", ConverterTool),
    ("file_conv", "📁", FileConverterTool),
    ("calculator","🧮", CalculatorTool),
    ("clock",     "🕐", ClockTool),
    ("password",  "🔑", PasswordTool),
    ("encoder",   "🔐", EncoderTool),
    ("colors",    "🎨", ColorTool),
    ("metadata",  "🔍", MetadataTool),
    ("media",     "▶️", MediaTool),
    ("youtube",   "▶", YoutubeTool),
]


class SidebarButton(QPushButton):
    def __init__(self, icon, label, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._icon = icon
        self._label = label
        self.setCheckable(True)
        self.setMinimumHeight(56)
        self.setText(f"  {icon}  {label}")
        self.setObjectName("sidebar_btn")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._dark = True
        self._lang_code = "fr"
        self._theme = DARK
        self._lang = TRANSLATIONS["fr"]
        self._tool_instances = {}
        self._sidebar_btns = []

        self.setWindowTitle(self._lang["app_title"])
        self.setMinimumSize(1000, 680)
        self.resize(1200, 760)

        self._build()
        self._apply_stylesheet()
        self._select_tool(0)

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(210)
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo
        logo = QLabel(f"  🧰  {self._lang['app_title']}")
        logo.setObjectName("logo")
        logo.setMinimumHeight(64)
        logo.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        sb_layout.addWidget(logo)

        # Boutons outils
        self._btn_group = []
        for i, (key, icon, _cls) in enumerate(TOOLS):
            btn = SidebarButton(icon, self._lang[key])
            btn.clicked.connect(lambda _, idx=i: self._select_tool(idx))
            sb_layout.addWidget(btn)
            self._sidebar_btns.append(btn)

        sb_layout.addStretch()

        # Toggle thème
        self.btn_theme = QPushButton(f"🌙  {self._lang['theme_dark']}")
        self.btn_theme.setObjectName("theme_btn")
        self.btn_theme.setMinimumHeight(44)
        self.btn_theme.clicked.connect(self._toggle_theme)
        sb_layout.addWidget(self.btn_theme)

        # Toggle langue
        self.btn_lang = QPushButton(f"🌐  {self._lang['lang_btn']}")
        self.btn_lang.setObjectName("theme_btn")
        self.btn_lang.setMinimumHeight(44)
        self.btn_lang.clicked.connect(self._toggle_lang)
        sb_layout.addWidget(self.btn_lang)

        sb_layout.addSpacing(10)

        # ── Content area ──────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setObjectName("content")

        for key, icon, Cls in TOOLS:
            widget = Cls(self._theme, self._lang)
            self._tool_instances[key] = widget
            self.stack.addWidget(widget)

        # ── Header ────────────────────────────────────────────────────────────
        content_wrapper = QWidget()
        cw_layout = QVBoxLayout(content_wrapper)
        cw_layout.setContentsMargins(0, 0, 0, 0)
        cw_layout.setSpacing(0)

        self.header = QLabel()
        self.header.setObjectName("header")
        self.header.setMinimumHeight(64)
        self.header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        cw_layout.addWidget(self.header)
        cw_layout.addWidget(self.stack)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_wrapper, 1)

    def _select_tool(self, idx):
        for i, btn in enumerate(self._sidebar_btns):
            btn.setChecked(i == idx)

        self.stack.setCurrentIndex(idx)
        key, icon, _ = TOOLS[idx]
        self.header.setText(f"   {icon}  {self._lang[key]}")

    def _toggle_theme(self):
        self._dark = not self._dark
        self._theme = DARK if self._dark else LIGHT
        label = self._lang["theme_dark"] if self._dark else self._lang["theme_light"]
        icon = "🌙" if self._dark else "☀️"
        self.btn_theme.setText(f"{icon}  {label}")
        self._apply_stylesheet()
        for inst in self._tool_instances.values():
            inst.apply_theme(self._theme, self._lang)

    def _toggle_lang(self):
        self._lang_code = "en" if self._lang_code == "fr" else "fr"
        self._lang = TRANSLATIONS[self._lang_code]
        self._update_texts()
        for inst in self._tool_instances.values():
            inst.apply_theme(self._theme, self._lang)

    def _update_texts(self):
        self.setWindowTitle(self._lang["app_title"])
        for i, (key, icon, _) in enumerate(TOOLS):
            self._sidebar_btns[i].setText(f"  {icon}  {self._lang[key]}")
        lang_icon = "🌙" if self._dark else "☀️"
        label = self._lang["theme_dark"] if self._dark else self._lang["theme_light"]
        self.btn_theme.setText(f"{lang_icon}  {label}")
        self.btn_lang.setText(f"🌐  {self._lang['lang_btn']}")
        idx = self.stack.currentIndex()
        key, icon, _ = TOOLS[idx]
        self.header.setText(f"   {icon}  {self._lang[key]}")

    def _apply_stylesheet(self):
        t = self._theme
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {t['bg']};
                color: {t['text']};
                font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
                font-size: 13px;
            }}
            QWidget#sidebar {{
                background-color: {t['sidebar']};
                border-right: 1px solid {t['border']};
            }}
            QWidget#content {{
                background-color: {t['bg']};
            }}
            QLabel#logo {{
                background-color: {t['sidebar']};
                color: {t['accent']};
                font-size: 16px;
                font-weight: bold;
                border-bottom: 1px solid {t['border']};
                padding-left: 8px;
            }}
            QLabel#header {{
                background-color: {t['card']};
                color: {t['text']};
                font-size: 18px;
                font-weight: bold;
                border-bottom: 1px solid {t['border']};
                padding-left: 10px;
            }}
            QPushButton#sidebar_btn {{
                background-color: transparent;
                color: {t['subtext']};
                border: none;
                border-radius: 0;
                text-align: left;
                padding-left: 16px;
                font-size: 13px;
            }}
            QPushButton#sidebar_btn:hover {{
                background-color: {t['highlight']};
                color: {t['text']};
            }}
            QPushButton#sidebar_btn:checked {{
                background-color: {t['highlight']};
                color: {t['accent']};
                border-left: 3px solid {t['accent']};
                font-weight: bold;
            }}
            QPushButton#theme_btn {{
                background-color: transparent;
                color: {t['subtext']};
                border: none;
                border-top: 1px solid {t['border']};
                text-align: left;
                padding-left: 16px;
                border-radius: 0;
            }}
            QPushButton#theme_btn:hover {{
                background-color: {t['highlight']};
                color: {t['text']};
            }}
            QPushButton {{
                background-color: {t['btn']};
                color: {t['btn_text']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {t['btn_hover']};
            }}
            QPushButton:disabled {{
                background-color: {t['border']};
                color: {t['subtext']};
            }}
            QPushButton#btn_equal {{
                background-color: {t['accent']};
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton#btn_equal:hover {{
                background-color: {t['btn_hover']};
            }}
            QPushButton#btn_op {{
                background-color: {t['accent2']};
                color: white;
            }}
            QPushButton#btn_func {{
                background-color: {t['card2']};
                color: {t['text']};
            }}
            QPushButton#svg_btn {{
                background-color: transparent;
                padding: 0px;
                border-radius: 999px;
            }}
            QPushButton#svg_btn:hover {{
                background-color: transparent;
            }}
            QLineEdit {{
                background-color: {t['input_bg']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {t['accent']};
            }}
            QTextEdit {{
                background-color: {t['input_bg']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }}
            QComboBox {{
                background-color: {t['input_bg']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t['card']};
                color: {t['text']};
                selection-background-color: {t['accent']};
                border: 1px solid {t['border']};
            }}
            QSpinBox {{
                background-color: {t['input_bg']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 4px 8px;
            }}
            QTabWidget::pane {{
                border: 1px solid {t['border']};
                border-radius: 8px;
                background-color: {t['card']};
            }}
            QTabBar::tab {{
                background-color: {t['card2']};
                color: {t['subtext']};
                padding: 8px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {t['accent']};
                color: white;
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {t['highlight']};
                color: {t['text']};
            }}
            QTableWidget {{
                background-color: {t['card']};
                color: {t['text']};
                gridline-color: {t['border']};
                border: 1px solid {t['border']};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {t['card2']};
                color: {t['subtext']};
                border: none;
                padding: 6px;
                font-weight: bold;
            }}
            QListWidget {{
                background-color: {t['card']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
            }}
            QListWidget::item:hover {{
                background-color: {t['highlight']};
            }}
            QScrollBar:vertical {{
                background: {t['card']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {t['border']};
                border-radius: 4px;
            }}
            QFrame#detail_card {{
                background-color: {t['card2']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 6px;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Toolbox")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()