from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os
import re


FORMATS = {
    "Audio": {
        "MP3":  {"ext": "mp3",  "type": "audio"},
        "AAC":  {"ext": "aac",  "type": "audio"},
        "FLAC": {"ext": "flac", "type": "audio"},
        "OGG":  {"ext": "ogg",  "type": "audio"},
        "WAV":  {"ext": "wav",  "type": "audio"},
        "M4A":  {"ext": "m4a",  "type": "audio"},
        "OPUS": {"ext": "opus", "type": "audio"},
        "WMA":  {"ext": "wma",  "type": "audio"},
    },
    "Vidéo": {
        "MP4":  {"ext": "mp4",  "type": "video"},
        "MKV":  {"ext": "mkv",  "type": "video"},
        "WEBM": {"ext": "webm", "type": "video"},
        "AVI":  {"ext": "avi",  "type": "video"},
        "MOV":  {"ext": "mov",  "type": "video"},
        "FLV":  {"ext": "flv",  "type": "video"},
        "TS":   {"ext": "ts",   "type": "video"},
        "3GP":  {"ext": "3gp",  "type": "video"},
    },
}

QUALITIES_AUDIO = ["320k", "256k", "192k", "128k", "96k", "64k"]
QUALITIES_VIDEO = ["Best", "1080p", "720p", "480p", "360p", "240p"]


class DownloadThread(QThread):
    progress = pyqtSignal(str)
    done     = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, url, fmt_info, quality, out_dir, filename):
        super().__init__()
        self.url      = url
        self.fmt_info = fmt_info
        self.quality  = quality
        self.out_dir  = out_dir
        self.filename = filename

    def run(self):
        try:
            import yt_dlp

            ext  = self.fmt_info["ext"]
            kind = self.fmt_info["type"]
            name = self.filename.strip() or "%(title)s"
            outtmpl = os.path.join(self.out_dir, f"{name}.%(ext)s")

            def hook(d):
                import re
                def strip_ansi(s):
                    return re.sub(r'\x1b\[[0-9;]*m', '', s or "")
                
                if d["status"] == "downloading":
                    pct = strip_ansi(d.get("_percent_str", ""))
                    spd = strip_ansi(d.get("_speed_str", ""))
                    eta = strip_ansi(d.get("_eta_str", ""))
                    self.progress.emit(f"Téléchargement : {pct}  |  Vitesse : {spd}  |  ETA : {eta}")
                elif d["status"] == "finished":
                    self.progress.emit("Conversion en cours...")

            ydl_opts = {
                "outtmpl":          outtmpl,
                "progress_hooks":   [hook],
                "quiet":            True,
                "no_warnings":      True,
                "no_color":       True,
            }

            if kind == "audio":
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key":              "FFmpegExtractAudio",
                        "preferredcodec":   ext,
                        "preferredquality": self.quality.rstrip("k"),
                    }],
                })
            else:
                q = self.quality
                if q == "best":
                    fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                else:
                    h = q.rstrip("p")
                    fmt = f"bestvideo[ext=mp4][height<={h}]+bestaudio[ext=m4a]/best[ext=mp4][height<={h}]/best"
                ydl_opts.update({
                    "format":              fmt,
                    "merge_output_format": ext,
                    "postprocessors": [{
                        "key":            "FFmpegVideoRemuxer",
                        "preferedformat": ext,
                    }],
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                title = info.get("title", "fichier")

            self.done.emit(title)

        except ImportError:
            self.error.emit("yt-dlp non installé.\nLancez : pip install yt-dlp")
        except Exception as e:
            self.error.emit(str(e))


class InfoThread(QThread):
    done  = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
            self.done.emit({
                "title":     info.get("title", "Inconnu"),
                "uploader":  info.get("uploader", "Inconnu"),
                "duration":  info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "views":     info.get("view_count", 0),
            })
        except Exception as e:
            self.error.emit(str(e))


class YoutubeTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang  = lang
        self._out_dir = os.path.expanduser("~/Downloads")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        # ── URL ───────────────────────────────────────────────────────────────
        layout.addWidget(QLabel("URL YouTube (ou autre plateforme supportée) :"))
        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setMinimumHeight(44)
        self.url_input.returnPressed.connect(self._fetch_info)
        self.btn_info = QPushButton("Analyser")
        self.btn_info.setMinimumHeight(44)
        self.btn_info.clicked.connect(self._fetch_info)
        url_row.addWidget(self.url_input, 1)
        url_row.addWidget(self.btn_info)
        layout.addLayout(url_row)

        # ── Info vidéo ────────────────────────────────────────────────────────
        self.info_card = QFrame()
        self.info_card.setObjectName("detail_card")
        self.info_card.setVisible(False)
        info_layout = QHBoxLayout(self.info_card)

        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(120, 68)
        self.lbl_thumb.setStyleSheet("border-radius: 6px; background: #000;")
        info_layout.addWidget(self.lbl_thumb)

        info_text = QVBoxLayout()
        self.lbl_title    = QLabel()
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_title.setWordWrap(True)
        self.lbl_uploader = QLabel()
        self.lbl_uploader.setStyleSheet("color: gray; font-size: 12px;")
        self.lbl_meta     = QLabel()
        self.lbl_meta.setStyleSheet("color: gray; font-size: 11px;")
        info_text.addWidget(self.lbl_title)
        info_text.addWidget(self.lbl_uploader)
        info_text.addWidget(self.lbl_meta)
        info_layout.addLayout(info_text, 1)
        layout.addWidget(self.info_card)

        # ── Options ───────────────────────────────────────────────────────────
        opts = QGridLayout()
        opts.setSpacing(10)

        # Catégorie
        opts.addWidget(QLabel("Catégorie :"), 0, 0)
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(list(FORMATS.keys()))
        self.cat_combo.setMinimumHeight(40)
        self.cat_combo.currentTextChanged.connect(self._on_cat_change)
        opts.addWidget(self.cat_combo, 0, 1)

        # Format
        opts.addWidget(QLabel("Format :"), 0, 2)
        self.fmt_combo = QComboBox()
        self.fmt_combo.setMinimumHeight(40)
        opts.addWidget(self.fmt_combo, 0, 3)

        # Qualité
        opts.addWidget(QLabel("Qualité :"), 1, 0)
        self.qual_combo = QComboBox()
        self.qual_combo.setMinimumHeight(40)
        opts.addWidget(self.qual_combo, 1, 1)

        # Nom de fichier
        opts.addWidget(QLabel("Nom du fichier :"), 1, 2)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Laisser vide = titre original")
        self.name_input.setMinimumHeight(40)
        opts.addWidget(self.name_input, 1, 3)

        layout.addLayout(opts)

        # ── Dossier de sortie ─────────────────────────────────────────────────
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Dossier de sortie :"))
        self.dir_label = QLabel(self._out_dir)
        self.dir_label.setStyleSheet("color: gray; font-size: 12px;")
        btn_dir = QPushButton("Changer")
        btn_dir.setMinimumHeight(36)
        btn_dir.clicked.connect(self._choose_dir)
        dir_row.addWidget(self.dir_label, 1)
        dir_row.addWidget(btn_dir)
        layout.addLayout(dir_row)

        # ── Bouton télécharger ────────────────────────────────────────────────
        self.btn_dl = QPushButton("Télécharger")
        self.btn_dl.setMinimumHeight(50)
        self.btn_dl.setObjectName("btn_equal")
        self.btn_dl.clicked.connect(self._download)
        layout.addWidget(self.btn_dl)

        # ── Progress ──────────────────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # ── Historique ────────────────────────────────────────────────────────
        layout.addWidget(QLabel("Historique :"))
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(120)
        layout.addWidget(self.history_list)

        # Note ffmpeg
        note = QLabel("ℹ️  Nécessite ffmpeg dans le PATH et yt-dlp installé (pip install yt-dlp)")
        note.setStyleSheet("color: gray; font-size: 11px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()
        self._on_cat_change("Audio")

    # ── Logique ───────────────────────────────────────────────────────────────
    def _on_cat_change(self, cat):
        self.fmt_combo.clear()
        self.fmt_combo.addItems(list(FORMATS[cat].keys()))
        self.qual_combo.clear()
        if cat == "Audio":
            self.qual_combo.addItems(QUALITIES_AUDIO)
            self.qual_combo.setCurrentText("192k")
        else:
            self.qual_combo.addItems(QUALITIES_VIDEO)
            self.qual_combo.setCurrentText("720p")

    def _choose_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Dossier de sortie", self._out_dir)
        if d:
            self._out_dir = d
            self.dir_label.setText(d)

    def _fetch_info(self):
        url = self.url_input.text().strip()
        if not url:
            return
        self.btn_info.setEnabled(False)
        self.status_label.setText("Récupération des infos...")
        self._info_thread = InfoThread(url)
        self._info_thread.done.connect(self._on_info)
        self._info_thread.error.connect(self._on_info_error)
        self._info_thread.start()

    def _on_info(self, info):
        self.btn_info.setEnabled(True)
        self.status_label.clear()
        self.info_card.setVisible(True)
        self.lbl_title.setText(info["title"])
        self.lbl_uploader.setText(info["uploader"])
        dur = info["duration"]
        m, s = divmod(dur, 60)
        h, m = divmod(m, 60)
        dur_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        views = f"{info['views']:,}".replace(",", " ")
        self.lbl_meta.setText(f"Durée : {dur_str}  |  Vues : {views}")

        # Thumbnail
        if info["thumbnail"]:
            self._thumb_thread = _ThumbThread(info["thumbnail"])
            self._thumb_thread.done.connect(self._set_thumb)
            self._thumb_thread.start()

    def _set_thumb(self, pixmap):
        self.lbl_thumb.setPixmap(
            pixmap.scaled(120, 68, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation))

    def _on_info_error(self, err):
        self.btn_info.setEnabled(True)
        self.status_label.setText(f"Erreur : {err}")

    def _download(self):
        url = self.url_input.text().strip()
        if not url:
            self.status_label.setText("Entrez une URL.")
            return
        cat     = self.cat_combo.currentText()
        fmt_key = self.fmt_combo.currentText()
        fmt_info = FORMATS[cat][fmt_key]
        quality  = self.qual_combo.currentText()
        filename = self.name_input.text().strip()

        self.btn_dl.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Démarrage...")

        self._dl_thread = DownloadThread(url, fmt_info, quality, self._out_dir, filename)
        self._dl_thread.progress.connect(self.status_label.setText)
        self._dl_thread.done.connect(self._on_done)
        self._dl_thread.error.connect(self._on_error)
        self._dl_thread.start()

    def _on_done(self, title):
        self.btn_dl.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✅ Terminé : {title}")
        cat = self.cat_combo.currentText()
        fmt = self.fmt_combo.currentText()
        self.history_list.insertItem(0, f"{title}  [{fmt}]")

    def _on_error(self, err):
        self.btn_dl.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"❌ Erreur : {err}")

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang  = lang


class _ThumbThread(QThread):
    done = pyqtSignal(object)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            import urllib.request
            from PyQt6.QtGui import QPixmap
            data = urllib.request.urlopen(self.url, timeout=5).read()
            pix = QPixmap()
            pix.loadFromData(data)
            self.done.emit(pix)
        except Exception:
            pass