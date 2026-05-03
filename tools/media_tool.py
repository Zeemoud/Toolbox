from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QUrl, QTime, QByteArray
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtSvgWidgets import QSvgWidget
import os

SUPPORTED = "Médias (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.mp4 *.avi *.mkv *.mov *.wmv *.webm *.ts)"

# ── SVG Icons ─────────────────────────────────────────────────────────────────
def svg(path_d, color="#ffffff", vb="0 0 24 24"):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"><path fill="{color}" d="{path_d}"/></svg>'

ICONS = {
    "play":    "M8 5v14l11-7z",
    "pause":   "M6 19h4V5H6v14zm8-14v14h4V5h-4z",
    "stop":    "M6 6h12v12H6z",
    "prev":    "M6 6h2v12H6zm3.5 6 8.5 6V6z",
    "next":    "M6 18l8.5-6L6 6v12zm2-12h2v12H8z",
    "vol":     "M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0 0 14 7.97v8.05c1.48-.73 2.5-2.25 2.5-4.02z",
    "mute":    "M16.5 12A4.5 4.5 0 0 0 14 7.97v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51A8.796 8.796 0 0 0 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3 3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06A8.99 8.99 0 0 0 17.73 18l2 2L21 18.73l-9-9L4.27 3zM12 4 9.91 6.09 12 8.18V4z",
    "shuffle": "M10.59 9.17 5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z",
    "repeat":  "M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z",
    "add":   "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z",
    "trash": "M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z",
}


def _set_icon(btn, icon_key, icon_size=20, color="#ffffff"):
    old_layout = btn.layout()
    if old_layout:
        while old_layout.count():
            item = old_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    else:
        old_layout = QHBoxLayout(btn)
        old_layout.setContentsMargins(0, 0, 0, 0)

    svg_str = svg(ICONS[icon_key], color=color)
    icon_widget = QSvgWidget()
    icon_widget.load(QByteArray(svg_str.encode()))
    icon_widget.setFixedSize(icon_size, icon_size)
    icon_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    old_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)


def make_icon_btn(icon_key, size=40, icon_size=20, checkable=False):
    btn = QPushButton()
    btn.setFixedSize(size, size)
    btn.setCheckable(checkable)
    btn.setObjectName("icon_btn")
    _set_icon(btn, icon_key, icon_size)
    return btn


def fmt_time(ms):
    if ms < 0:
        return "0:00"
    t = QTime(0, 0).addMSecs(int(ms))
    return t.toString("m:ss") if ms < 3600000 else t.toString("h:mm:ss")


class MediaTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._playlist = []
        self._current_idx = -1
        self._was_playing = False
        self._build()
        self.setAcceptDrops(True)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # ── Player ────────────────────────────────────────────────────────────
        self.player = QMediaPlayer()
        self.audio_out = QAudioOutput()
        self.player.setAudioOutput(self.audio_out)
        self.audio_out.setVolume(0.7)

        # ── Zone vidéo ────────────────────────────────────────────────────────
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(240)
        self.video_widget.setStyleSheet("background: #000; border-radius: 10px;")
        self.player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)

        self.audio_placeholder = QLabel("♪")
        self.audio_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_placeholder.setStyleSheet(
            "background: #12151f; border-radius: 10px; font-size: 64px;"
            "color: #333; min-height: 240px;"
        )
        self.audio_placeholder.setVisible(False)
        layout.addWidget(self.audio_placeholder)

        # Titre
        self.title_label = QLabel("Aucun fichier")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # ── Barre de progression ──────────────────────────────────────────────
        seek_row = QHBoxLayout()
        self.time_label = QLabel("0:00")
        self.time_label.setFixedWidth(45)
        self.time_label.setStyleSheet("color: gray; font-size: 11px;")

        self.seek_bar = QSlider(Qt.Orientation.Horizontal)
        self.seek_bar.setRange(0, 0)
        self.seek_bar.sliderMoved.connect(self._seek)
        self.seek_bar.sliderPressed.connect(
            lambda: setattr(self, '_was_playing',
                self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
        )
        self.seek_bar.sliderReleased.connect(self._on_seek_release)

        self.dur_label = QLabel("0:00")
        self.dur_label.setFixedWidth(45)
        self.dur_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.dur_label.setStyleSheet("color: gray; font-size: 11px;")

        seek_row.addWidget(self.time_label)
        seek_row.addWidget(self.seek_bar, 1)
        seek_row.addWidget(self.dur_label)
        layout.addLayout(seek_row)

        # ── Contrôles ─────────────────────────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.setSpacing(6)

        self.btn_shuffle = make_icon_btn("shuffle", 36, 18, checkable=True)
        self.btn_prev    = make_icon_btn("prev",    44, 22)
        self.btn_play    = make_icon_btn("play",    56, 28)
        self.btn_next    = make_icon_btn("next",    44, 22)
        self.btn_repeat  = make_icon_btn("repeat",  36, 18, checkable=True)

        self.btn_shuffle.clicked.connect(lambda: None)
        self.btn_prev.clicked.connect(self._prev)
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_next.clicked.connect(self._next)
        self.btn_stop    = make_icon_btn("stop", 36, 18)
        self.btn_stop.clicked.connect(self._stop)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedHeight(32)
        sep.setStyleSheet("color: #2a2d45;")

        self.btn_mute = make_icon_btn("vol", 36, 18, checkable=True)
        self.btn_mute.clicked.connect(self._toggle_mute)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(70)
        self.vol_slider.setFixedWidth(90)
        self.vol_slider.valueChanged.connect(lambda v: self.audio_out.setVolume(v / 100))

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFixedHeight(32)
        sep2.setStyleSheet("color: #2a2d45;")

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "0.75x", "1x", "1.25x", "1.5x", "2x"])
        self.speed_combo.setCurrentText("1x")
        self.speed_combo.setFixedWidth(70)
        self.speed_combo.setMinimumHeight(36)
        self.speed_combo.currentTextChanged.connect(
            lambda t: self.player.setPlaybackRate(float(t.rstrip("x")))
        )

        ctrl.addStretch()
        ctrl.addWidget(self.btn_shuffle)
        ctrl.addWidget(self.btn_prev)
        ctrl.addWidget(self.btn_play)
        ctrl.addWidget(self.btn_next)
        ctrl.addWidget(self.btn_repeat)
        ctrl.addWidget(self.btn_stop)
        ctrl.addWidget(sep)
        ctrl.addWidget(self.btn_mute)
        ctrl.addWidget(self.vol_slider)
        ctrl.addWidget(sep2)
        ctrl.addWidget(QLabel("Vitesse:"))
        ctrl.addWidget(self.speed_combo)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Style boutons icônes
        self.setStyleSheet(self.styleSheet() + """
            QPushButton#icon_btn {
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }
            QPushButton#icon_btn:hover {
                background-color: rgba(124, 106, 247, 0.2);
            }
            QPushButton#icon_btn:checked {
                background-color: rgba(124, 106, 247, 0.4);
            }
            QPushButton#icon_btn:pressed {
                background-color: rgba(124, 106, 247, 0.6);
            }
        """)

        # ── Playlist ──────────────────────────────────────────────────────────
        pl_header = QHBoxLayout()
        pl_header.addWidget(QLabel("Playlist"))
        pl_header.addStretch()

        btn_add = make_icon_btn("add", 32, 16)
        btn_add.setToolTip("Ajouter des fichiers")
        btn_add.clicked.connect(self._add_files)

        btn_clear_pl = make_icon_btn("trash", 32, 16)
        btn_clear_pl.setToolTip("Vider la playlist")
        btn_clear_pl.clicked.connect(self._clear_playlist)

        pl_header.addWidget(btn_add)
        pl_header.addWidget(btn_clear_pl)
        layout.addLayout(pl_header)

        self.playlist_widget = QListWidget()
        self.playlist_widget.setMaximumHeight(150)
        self.playlist_widget.itemDoubleClicked.connect(self._on_playlist_dclick)
        self.playlist_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_widget.customContextMenuRequested.connect(self._playlist_context)
        layout.addWidget(self.playlist_widget)

        # Signaux player
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.mediaStatusChanged.connect(self._on_status)

    # ── Drag & Drop ───────────────────────────────────────────────────────────
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                self._add_to_playlist(path)
        if self._current_idx == -1 and self._playlist:
            self._play_index(0)

    # ── Playlist ──────────────────────────────────────────────────────────────
    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Ajouter des fichiers", "", SUPPORTED)
        for p in paths:
            self._add_to_playlist(p)
        if self._current_idx == -1 and self._playlist:
            self._play_index(0)

    def _add_to_playlist(self, path):
        self._playlist.append(path)
        self.playlist_widget.addItem(os.path.basename(path))

    def _clear_playlist(self):
        self._stop()
        self._playlist.clear()
        self._current_idx = -1
        self.playlist_widget.clear()
        self.title_label.setText("Aucun fichier")

    def _on_playlist_dclick(self, item):
        self._play_index(self.playlist_widget.row(item))

    def _playlist_context(self, pos):
        item = self.playlist_widget.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        act_play   = menu.addAction("Lire")
        act_remove = menu.addAction("Supprimer")
        action = menu.exec(self.playlist_widget.mapToGlobal(pos))
        idx = self.playlist_widget.row(item)
        if action == act_play:
            self._play_index(idx)
        elif action == act_remove:
            self._playlist.pop(idx)
            self.playlist_widget.takeItem(idx)
            if self._current_idx == idx:
                self._stop()
                self._current_idx = -1

    # ── Lecture ───────────────────────────────────────────────────────────────
    def _play_index(self, idx):
        if 0 <= idx < len(self._playlist):
            self._current_idx = idx
            path = self._playlist[idx]
            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()
            self.title_label.setText(os.path.basename(path))
            self.playlist_widget.setCurrentRow(idx)
            ext = os.path.splitext(path)[1].lower()
            is_video = ext in ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm', '.ts')
            self.video_widget.setVisible(is_video)
            self.audio_placeholder.setVisible(not is_video)

    def _toggle_play(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()
        else:
            if self._playlist:
                self._play_index(max(self._current_idx, 0))

    def _stop(self):
        self.player.stop()

    def _prev(self):
        if self._current_idx > 0:
            self._play_index(self._current_idx - 1)

    def _next(self):
        import random
        if not self._playlist:
            return
        if self.btn_shuffle.isChecked():
            idx = random.randint(0, len(self._playlist) - 1)
        else:
            idx = self._current_idx + 1
        if idx < len(self._playlist):
            self._play_index(idx)
        elif self.btn_repeat.isChecked():
            self._play_index(0)

    def _seek(self, value):
        self.player.setPosition(value)

    def _on_seek_release(self):
        self.player.setPosition(self.seek_bar.value())
        if self._was_playing:
            self.player.play()

    def _toggle_mute(self, checked):
        self.audio_out.setMuted(checked)
        _set_icon(self.btn_mute, "mute" if checked else "vol", 18)

    def _on_position(self, pos):
        self.seek_bar.blockSignals(True)
        self.seek_bar.setValue(pos)
        self.seek_bar.blockSignals(False)
        self.time_label.setText(fmt_time(pos))

    def _on_duration(self, dur):
        self.seek_bar.setRange(0, dur)
        self.dur_label.setText(fmt_time(dur))

    def _on_state(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        _set_icon(self.btn_play, "pause" if playing else "play", 28)

    def _on_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._next()

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang