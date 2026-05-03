from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
import os
import datetime


class MetaThread(QThread):
    done = pyqtSignal(dict, str)
    error = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            meta = {}
            path = self.path
            ext = os.path.splitext(path)[1].lower()

            # Infos fichier de base
            stat = os.stat(path)
            meta["📁 Fichier"] = {
                "Nom": os.path.basename(path),
                "Chemin": path,
                "Taille": self._fmt_size(stat.st_size),
                "Modifié": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                "Créé": datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%d/%m/%Y %H:%M:%S"),
                "Extension": ext,
            }

            # Image
            if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'):
                try:
                    from PIL import Image
                    from PIL.ExifTags import TAGS, GPSTAGS
                    img = Image.open(path)
                    meta["🖼️ Image"] = {
                        "Dimensions": f"{img.width} × {img.height} px",
                        "Mode": img.mode,
                        "Format": img.format or ext.upper(),
                        "Mégapixels": f"{(img.width * img.height) / 1_000_000:.2f} MP",
                    }
                    exif_data = img._getexif() if hasattr(img, '_getexif') else None
                    if exif_data:
                        exif = {}
                        gps_info = {}
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)
                            if tag == "GPSInfo":
                                for gps_tag, gps_val in value.items():
                                    gps_name = GPSTAGS.get(gps_tag, gps_tag)
                                    gps_info[gps_name] = str(gps_val)
                            elif isinstance(value, (str, int, float)):
                                exif[str(tag)] = str(value)[:100]
                        if exif:
                            keep = ["Make", "Model", "DateTime", "ExposureTime", "FNumber",
                                    "ISOSpeedRatings", "FocalLength", "Flash", "Software",
                                    "Artist", "Copyright", "Orientation"]
                            meta["📷 EXIF"] = {k: v for k, v in exif.items() if k in keep}
                            if not meta["📷 EXIF"]:
                                meta["📷 EXIF"] = {k: v for k, v in list(exif.items())[:15]}
                        if gps_info:
                            meta["🌍 GPS"] = gps_info
                except Exception as e:
                    meta["🖼️ Image"] = {"Erreur": str(e)}

            # Audio
            elif ext in ('.mp3', '.flac', '.ogg', '.wav', '.m4a', '.aac'):
                try:
                    import mutagen
                    from mutagen import File as MutagenFile
                    audio = MutagenFile(path)
                    if audio:
                        audio_meta = {}
                        if hasattr(audio, 'info'):
                            info = audio.info
                            if hasattr(info, 'length'):
                                mins, secs = divmod(int(info.length), 60)
                                audio_meta["Durée"] = f"{mins}:{secs:02d}"
                            if hasattr(info, 'bitrate'):
                                audio_meta["Bitrate"] = f"{info.bitrate // 1000} kbps"
                            if hasattr(info, 'sample_rate'):
                                audio_meta["Sample rate"] = f"{info.sample_rate} Hz"
                            if hasattr(info, 'channels'):
                                audio_meta["Canaux"] = str(info.channels)
                        meta["🎵 Audio"] = audio_meta
                        tags = {}
                        for k, v in audio.tags.items() if audio.tags else []:
                            tags[str(k)] = str(v)[:100]
                        if tags:
                            meta["🏷️ Tags"] = dict(list(tags.items())[:20])
                except ImportError:
                    meta["🎵 Audio"] = {"Note": "Installez mutagen pour les métadonnées audio"}
                except Exception as e:
                    meta["🎵 Audio"] = {"Erreur": str(e)}

            # PDF
            elif ext == '.pdf':
                try:
                    import pypdf
                    with open(path, 'rb') as f:
                        reader = pypdf.PdfReader(f)
                        info = reader.metadata
                        pdf_meta = {
                            "Pages": str(len(reader.pages)),
                        }
                        if info:
                            for k, v in info.items():
                                clean_key = k.lstrip('/')
                                pdf_meta[clean_key] = str(v)[:100]
                        meta["📄 PDF"] = pdf_meta
                except ImportError:
                    meta["📄 PDF"] = {"Note": "Installez pypdf pour les métadonnées PDF"}
                except Exception as e:
                    meta["📄 PDF"] = {"Erreur": str(e)}

            # Vidéo
            elif ext in ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'):
                meta["🎬 Vidéo"] = {"Note": "Installez opencv-python pour les métadonnées vidéo"}

            self.done.emit(meta, path)
        except Exception as e:
            self.error.emit(str(e))

    def _fmt_size(self, n):
        for unit in ("o", "Ko", "Mo", "Go"):
            if abs(n) < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} To"


class MetadataTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        # Sélection fichier
        file_row = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Sélectionnez ou glissez un fichier...")
        self.file_input.setReadOnly(True)
        self.file_input.setMinimumHeight(44)
        btn_browse = QPushButton("Parcourir")
        btn_browse.setMinimumHeight(44)
        btn_browse.clicked.connect(self._browse)
        file_row.addWidget(self.file_input, 1)
        file_row.addWidget(btn_browse)
        layout.addLayout(file_row)

        hint = QLabel("Supporte : images (JPG, PNG, WEBP...), audio (MP3, FLAC...), PDF")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)

        # Contenu principal
        content = QHBoxLayout()

        # Aperçu
        self.preview = QLabel("Aperçu")
        self.preview.setFixedSize(200, 200)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("border: 1px solid #2a2d45; border-radius: 8px; color: gray;")
        content.addWidget(self.preview)

        # Arbre de métadonnées
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Propriété", "Valeur"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.setAlternatingRowColors(True)
        content.addWidget(self.tree, 1)
        layout.addLayout(content)

        # Boutons
        btns = QHBoxLayout()
        btn_copy_all = QPushButton("Tout copier")
        btn_copy_all.setMinimumHeight(40)
        btn_copy_all.clicked.connect(self._copy_all)
        btn_export = QPushButton("Exporter TXT")
        btn_export.setMinimumHeight(40)
        btn_export.clicked.connect(self._export)
        btns.addWidget(btn_copy_all)
        btns.addWidget(btn_export)
        btns.addStretch()
        layout.addLayout(btns)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self._load_file(urls[0].toLocalFile())

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un fichier", "",
            "Tous fichiers (*);;Images (*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff);;Audio (*.mp3 *.flac *.wav *.ogg *.m4a);;PDF (*.pdf)"
        )
        if path:
            self._load_file(path)

    def _load_file(self, path):
        self.file_input.setText(path)
        self.status.setText("Lecture des métadonnées...")
        self.tree.clear()
        self._load_preview(path)
        self._thread = MetaThread(path)
        self._thread.done.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _load_preview(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'):
            pix = QPixmap(path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
            self.preview.setPixmap(pix)
            self.preview.setText("")
        else:
            icons = {'.mp3': '🎵', '.flac': '🎵', '.wav': '🎵', '.ogg': '🎵',
                     '.pdf': '📄', '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬'}
            self.preview.setPixmap(QPixmap())
            self.preview.setText(icons.get(ext, "📁") + "\n" + os.path.basename(path))

    def _on_done(self, meta, path):
        self.status.clear()
        self.tree.clear()
        for section, props in meta.items():
            parent = QTreeWidgetItem(self.tree, [section, ""])
            parent.setExpanded(True)
            for key, value in props.items():
                QTreeWidgetItem(parent, [key, str(value)])

    def _on_error(self, err):
        self.status.setText(f"Erreur : {err}")

    def _copy_all(self):
        lines = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            section = root.child(i)
            lines.append(f"[{section.text(0)}]")
            for j in range(section.childCount()):
                item = section.child(j)
                lines.append(f"  {item.text(0)}: {item.text(1)}")
            lines.append("")
        QApplication.clipboard().setText('\n'.join(lines))
        self.status.setText("Copié !")

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter", "metadata.txt", "Texte (*.txt)")
        if path:
            lines = []
            root = self.tree.invisibleRootItem()
            for i in range(root.childCount()):
                section = root.child(i)
                lines.append(f"[{section.text(0)}]")
                for j in range(section.childCount()):
                    item = section.child(j)
                    lines.append(f"  {item.text(0)}: {item.text(1)}")
                lines.append("")
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            self.status.setText(f"Exporté : {path}")

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang