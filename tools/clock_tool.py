from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont
import datetime
import pytz

TIMEZONES = [
    ("Paris",        "Europe/Paris"),
    ("Londres",      "Europe/London"),
    ("New York",     "America/New_York"),
    ("Los Angeles",  "America/Los_Angeles"),
    ("Tokyo",        "Asia/Tokyo"),
    ("Dubaï",        "Asia/Dubai"),
    ("Sydney",       "Australia/Sydney"),
    ("São Paulo",    "America/Sao_Paulo"),
    ("Moscou",       "Europe/Moscow"),
    ("Pékin",        "Asia/Shanghai"),
    ("Mumbai",       "Asia/Kolkata"),
    ("Singapour",    "Asia/Singapore"),
]


class ClockTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._chrono_running = False
        self._chrono_ms = 0
        self._laps = []
        self._timer_remaining = 0
        self._timer_running = False
        self._build()

        self._tick = QTimer()
        self._tick.timeout.connect(self._update_all)
        self._tick.start(100)

        self._chrono_timer = QTimer()
        self._chrono_timer.timeout.connect(self._tick_chrono)

        self._countdown_timer = QTimer()
        self._countdown_timer.timeout.connect(self._tick_countdown)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_clock(), "Horloge")
        self.tabs.addTab(self._build_chrono(), "Chronomètre")
        self.tabs.addTab(self._build_timer(), "Minuteur")
        layout.addWidget(self.tabs)

    # ── Horloge ───────────────────────────────────────────────────────────────
    def _build_clock(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet("font-size: 64px; font-weight: bold;")
        layout.addWidget(self.lbl_time)

        self.lbl_date = QLabel("")
        self.lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_date.setStyleSheet("font-size: 16px; color: gray;")
        layout.addWidget(self.lbl_date)

        layout.addWidget(QLabel(self.lang["world_clock"]))

        self.world_table = QTableWidget(len(TIMEZONES), 3)
        self.world_table.setHorizontalHeaderLabels(["Ville", "Heure", "Fuseau"])
        self.world_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.world_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.world_table.verticalHeader().setVisible(False)
        for i, (city, tz) in enumerate(TIMEZONES):
            self.world_table.setItem(i, 0, QTableWidgetItem(city))
            self.world_table.setItem(i, 1, QTableWidgetItem(""))
            self.world_table.setItem(i, 2, QTableWidgetItem(tz))
        layout.addWidget(self.world_table)
        return w

    # ── Chronomètre ───────────────────────────────────────────────────────────
    def _build_chrono(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        self.chrono_display = QLabel("00:00.000")
        self.chrono_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chrono_display.setStyleSheet("font-size: 56px; font-weight: bold; font-family: monospace;")
        layout.addWidget(self.chrono_display)

        btns = QHBoxLayout()
        self.btn_start_stop = QPushButton(self.lang["start"])
        self.btn_start_stop.setMinimumHeight(50)
        self.btn_start_stop.setObjectName("btn_equal")
        self.btn_start_stop.clicked.connect(self._chrono_toggle)

        self.btn_lap = QPushButton(self.lang["lap"])
        self.btn_lap.setMinimumHeight(50)
        self.btn_lap.clicked.connect(self._chrono_lap)

        self.btn_reset = QPushButton(self.lang["reset"])
        self.btn_reset.setMinimumHeight(50)
        self.btn_reset.clicked.connect(self._chrono_reset)

        btns.addWidget(self.btn_start_stop, 2)
        btns.addWidget(self.btn_lap)
        btns.addWidget(self.btn_reset)
        layout.addLayout(btns)

        self.lap_list = QListWidget()
        layout.addWidget(self.lap_list)
        return w

    # ── Minuteur ──────────────────────────────────────────────────────────────
    def _build_timer(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)

        self.timer_display = QLabel("00:00")
        self.timer_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_display.setStyleSheet("font-size: 72px; font-weight: bold; font-family: monospace;")
        layout.addWidget(self.timer_display)

        # Presets
        presets = QHBoxLayout()
        for label, secs in [("1 min", 60), ("5 min", 300), ("10 min", 600),
                             ("15 min", 900), ("25 min", 1500), ("30 min", 1800)]:
            b = QPushButton(label)
            b.setMinimumHeight(36)
            b.clicked.connect(lambda _, s=secs: self._set_timer(s))
            presets.addWidget(b)
        layout.addLayout(presets)

        # Input manuel
        inp_row = QHBoxLayout()
        self.timer_input = QLineEdit("05:00")
        self.timer_input.setMinimumHeight(44)
        self.timer_input.setPlaceholderText("mm:ss")
        self.timer_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_input.setStyleSheet("font-size: 20px;")
        inp_row.addWidget(QLabel(self.lang["set_timer"]))
        inp_row.addWidget(self.timer_input, 1)
        layout.addLayout(inp_row)

        btns = QHBoxLayout()
        self.btn_timer_start = QPushButton(self.lang["start"])
        self.btn_timer_start.setMinimumHeight(50)
        self.btn_timer_start.setObjectName("btn_equal")
        self.btn_timer_start.clicked.connect(self._timer_toggle)

        self.btn_timer_reset = QPushButton(self.lang["reset"])
        self.btn_timer_reset.setMinimumHeight(50)
        self.btn_timer_reset.clicked.connect(self._timer_reset)

        btns.addWidget(self.btn_timer_start, 2)
        btns.addWidget(self.btn_timer_reset)
        layout.addLayout(btns)

        self.timer_status = QLabel("")
        self.timer_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_status.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.timer_status)
        layout.addStretch()
        return w

    # ── Logique Chrono ────────────────────────────────────────────────────────
    def _chrono_toggle(self):
        if self._chrono_running:
            self._chrono_timer.stop()
            self._chrono_running = False
            self.btn_start_stop.setText(self.lang["start"])
        else:
            self._chrono_timer.start(10)
            self._chrono_running = True
            self.btn_start_stop.setText(self.lang["stop"])

    def _tick_chrono(self):
        self._chrono_ms += 10
        self._update_chrono_display()

    def _update_chrono_display(self):
        ms = self._chrono_ms
        minutes = ms // 60000
        seconds = (ms % 60000) // 1000
        millis = ms % 1000
        self.chrono_display.setText(f"{minutes:02d}:{seconds:02d}.{millis:03d}")

    def _chrono_lap(self):
        if self._chrono_running:
            ms = self._chrono_ms
            minutes = ms // 60000
            seconds = (ms % 60000) // 1000
            millis = ms % 1000
            n = len(self._laps) + 1
            self._laps.append(ms)
            self.lap_list.addItem(f"Tour {n}: {minutes:02d}:{seconds:02d}.{millis:03d}")
            self.lap_list.scrollToBottom()

    def _chrono_reset(self):
        self._chrono_timer.stop()
        self._chrono_running = False
        self._chrono_ms = 0
        self._laps = []
        self.lap_list.clear()
        self.chrono_display.setText("00:00.000")
        self.btn_start_stop.setText(self.lang["start"])

    # ── Logique Timer ─────────────────────────────────────────────────────────
    def _set_timer(self, secs):
        self._timer_reset()
        m, s = divmod(secs, 60)
        self.timer_input.setText(f"{m:02d}:{s:02d}")
        self._timer_remaining = secs * 10  # en dixièmes de sec

    def _timer_toggle(self):
        if self._timer_running:
            self._countdown_timer.stop()
            self._timer_running = False
            self.btn_timer_start.setText(self.lang["start"])
        else:
            if self._timer_remaining == 0:
                try:
                    parts = self.timer_input.text().split(":")
                    m, s = int(parts[0]), int(parts[1])
                    self._timer_remaining = (m * 60 + s) * 10
                except Exception:
                    return
            self._countdown_timer.start(100)
            self._timer_running = True
            self.btn_timer_start.setText(self.lang["stop"])
            self.timer_status.clear()

    def _tick_countdown(self):
        self._timer_remaining -= 1
        if self._timer_remaining <= 0:
            self._timer_remaining = 0
            self._countdown_timer.stop()
            self._timer_running = False
            self.btn_timer_start.setText(self.lang["start"])
            self.timer_status.setText("⏰ Temps écoulé !")
        total_s = self._timer_remaining // 10
        m, s = divmod(total_s, 60)
        self.timer_display.setText(f"{m:02d}:{s:02d}")

    def _timer_reset(self):
        self._countdown_timer.stop()
        self._timer_running = False
        self._timer_remaining = 0
        self.timer_display.setText("00:00")
        self.btn_timer_start.setText(self.lang["start"])
        self.timer_status.clear()

    # ── Update global ─────────────────────────────────────────────────────────
    def _update_all(self):
        now = datetime.datetime.now()
        self.lbl_time.setText(now.strftime("%H:%M:%S"))
        self.lbl_date.setText(now.strftime("%A %d %B %Y").capitalize())

        for i, (_, tz) in enumerate(TIMEZONES):
            try:
                tz_obj = pytz.timezone(tz)
                t = datetime.datetime.now(tz_obj)
                self.world_table.item(i, 1).setText(t.strftime("%H:%M:%S"))
            except Exception:
                pass

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang