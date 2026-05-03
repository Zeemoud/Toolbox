from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os
import subprocess
import shutil

CATEGORIES = {

    "Archives": {
        "extensions": [
            ".7z", ".ace", ".alz", ".arc", ".arj", ".bz2", ".cab", ".cpio",
            ".deb", ".gz", ".jar", ".lha", ".lz", ".lzma", ".lzo", ".rar",
            ".rpm", ".tar", ".tar.7z", ".tar.bz", ".tar.bz2", ".tar.lz",
            ".tar.lzma", ".tar.lzo", ".tar.xz", ".tar.z", ".tbz2", ".tgz",
            ".xz", ".z", ".zip", ".zst",
        ],
        "formats": ["7Z", "TAR", "TAR.GZ", "TAR.BZ2", "TAR.XZ", "TBZ2", "TGZ", "ZIP"],
        "engine": "python_tarzip",
        "note": "7Z nécessite py7zr (pip install py7zr) · RAR/ACE/CAB : lecture seulement",
    },

    "Audio": {
        "extensions": [
            ".8svx", ".aac", ".ac3", ".aiff", ".aif", ".amb", ".amr", ".ape",
            ".au", ".avr", ".caf", ".cdda", ".cvs", ".cvsd", ".cvu", ".dss",
            ".dts", ".dvms", ".fap", ".flac", ".fssd", ".gsm", ".gsrt",
            ".hcom", ".htk", ".ima", ".ircam", ".m4a", ".m4r", ".maud",
            ".mp2", ".mp3", ".nist", ".oga", ".ogg", ".opus", ".paf", ".prc",
            ".pvf", ".ra", ".sd2", ".shn", ".sln", ".smp", ".snd", ".sndr",
            ".sndt", ".sou", ".sph", ".spx", ".tak", ".tta", ".txw", ".vms",
            ".voc", ".vox", ".vqf", ".w64", ".wav", ".wma", ".wv", ".wve", ".xa",
        ],
        "formats": [
            "AAC", "AC3", "AIFF", "AMR", "APE", "AU", "FLAC", "GSM",
            "M4A", "M4R", "MP2", "MP3", "OGA", "OGG", "OPUS", "RA",
            "SHN", "SND", "SPX", "TTA", "VOC", "W64", "WAV", "WMA", "WV",
        ],
        "engine": "ffmpeg",
        "note": "Nécessite ffmpeg dans le PATH",
    },

    "CAD": {
        "extensions": [".dxf"],
        "formats": ["DXF", "SVG", "PNG", "PDF"],
        "engine": "ezdxf",
        "note": "Nécessite ezdxf (pip install ezdxf matplotlib)",
    },

    "Documents": {
        "extensions": [
            ".abw", ".aw", ".csv", ".dbk", ".djvu", ".doc", ".docm", ".docx",
            ".dot", ".dotm", ".dotx", ".html", ".htm", ".kwd", ".odt", ".oxps",
            ".pdf", ".rtf", ".sxw", ".txt", ".wps", ".xls", ".xlsx", ".xps",
        ],
        "formats": [
            "CSV", "DOCX", "HTML", "ODT", "PDF", "RTF", "TXT", "XLS", "XLSX",
        ],
        "engine": "libreoffice_or_python",
        "note": "TXT↔HTML↔CSV : Python natif · DOCX/PDF/ODT nécessite LibreOffice",
    },

    "Images": {
        "extensions": [
            ".3fr", ".arw", ".avif", ".bmp", ".cr2", ".crw", ".cur", ".dcm",
            ".dcr", ".dds", ".dng", ".erf", ".exr", ".fax", ".fts", ".g3",
            ".g4", ".gif", ".gv", ".hdr", ".heic", ".heif", ".hrz", ".ico",
            ".iiq", ".ipl", ".jbg", ".jbig", ".jfi", ".jfif", ".jif", ".jnx",
            ".jp2", ".jpe", ".jpeg", ".jpg", ".jps", ".k25", ".kdc", ".mac",
            ".map", ".mef", ".mng", ".mrw", ".mtv", ".nef", ".nrw", ".orf",
            ".otb", ".pal", ".palm", ".pam", ".pbm", ".pcd", ".pct", ".pcx",
            ".pdb", ".pef", ".pes", ".pfm", ".pgm", ".pgx", ".picon", ".pict",
            ".pix", ".plasma", ".png", ".pnm", ".ppm", ".psd", ".pwp", ".raf",
            ".ras", ".rgb", ".rgba", ".rgbo", ".rgf", ".rla", ".rle", ".rw2",
            ".sct", ".sfw", ".sgi", ".six", ".sixel", ".sr2", ".srf", ".sun",
            ".svg", ".tga", ".tiff", ".tif", ".tim", ".tm2", ".uyvy", ".viff",
            ".vips", ".wbmp", ".webp", ".wmz", ".wpg", ".x3f", ".xbm", ".xc",
            ".xcf", ".xpm", ".xv", ".xwd", ".yuv",
        ],
        "formats": [
            "AVIF", "BMP", "DDS", "EXR", "GIF", "HEIC", "HDR", "ICO",
            "JP2", "JPEG", "JPG", "MNG", "PAM", "PBM", "PGM", "PNG",
            "PNM", "PPM", "PSD", "SGI", "TGA", "TIFF", "WBMP", "WEBP",
            "XBM", "XCF", "XPM", "YUV",
        ],
        "engine": "imagemagick_or_pil",
        "note": "PIL pour les formats courants · ImageMagick recommandé pour les formats RAW/exotiques",
    },

    "Livres électroniques": {
        "extensions": [
            ".azw3", ".epub", ".fb2", ".lrf", ".mobi", ".pdb", ".rb", ".snb", ".tcr",
        ],
        "formats": ["AZW3", "EPUB", "FB2", "LRF", "MOBI", "PDF", "TXT"],
        "engine": "calibre",
        "note": "Nécessite Calibre (ebook-convert) dans le PATH",
    },

    "Polices": {
        "extensions": [
            ".afm", ".bin", ".cff", ".cid", ".dfont", ".otf", ".pfa", ".pfb",
            ".ps", ".pt3", ".sfd", ".t11", ".t42", ".ttf", ".ufo", ".woff", ".woff2",
        ],
        "formats": ["CFF", "OTF", "TTF", "WOFF", "WOFF2"],
        "engine": "fonttools",
        "note": "Nécessite fonttools (pip install fonttools brotli)",
    },

    "Présentations": {
        "extensions": [
            ".odp", ".pot", ".potm", ".potx", ".pps", ".ppsm", ".ppsx",
            ".ppt", ".pptm", ".pptx",
        ],
        "formats": ["ODP", "PDF", "PPTX"],
        "engine": "libreoffice",
        "note": "Nécessite LibreOffice dans le PATH",
    },

    "Vecteurs": {
        "extensions": [
            ".aff", ".ai", ".ccx", ".cdr", ".cdt", ".cgm", ".cmx", ".dst",
            ".emf", ".eps", ".exp", ".fig", ".pcs", ".pes", ".plt", ".ps",
            ".sk", ".sk1", ".svg", ".wmf",
        ],
        "formats": ["EMF", "EPS", "PDF", "PNG", "PS", "SVG", "WMF"],
        "engine": "inkscape_or_imagemagick",
        "note": "Nécessite Inkscape ou ImageMagick dans le PATH",
    },

    "Vidéos": {
        "extensions": [
            ".3g2", ".3gp", ".aaf", ".asf", ".av1", ".avchd", ".avi", ".cavs",
            ".divx", ".dv", ".f4v", ".flv", ".hevc", ".m2ts", ".m2v", ".m4v",
            ".mjpeg", ".mkv", ".mod", ".mov", ".mp4", ".mpeg", ".mpg", ".mts",
            ".mxf", ".ogv", ".rm", ".rmvb", ".swf", ".tod", ".ts", ".vob",
            ".webm", ".wmv", ".wtv", ".xvid",
        ],
        "formats": [
            "3GP", "AVI", "DIVX", "DV", "F4V", "FLV", "M4V", "MKV", "MOD",
            "MOV", "MP4", "MPEG", "MPG", "MTS", "MXF", "OGV", "RM", "SWF",
            "TS", "VOB", "WEBM", "WMV",
        ],
        "engine": "ffmpeg",
        "note": "Nécessite ffmpeg dans le PATH",
    },
}


# ── Moteurs ───────────────────────────────────────────────────────────────────

def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "Erreur inconnue")


def convert_image(inp, out):
    ext = os.path.splitext(out)[1].lower()
    try:
        from PIL import Image
        img = Image.open(inp)
        if ext in (".jpg", ".jpeg") and img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        if ext == ".ico":
            img.save(out, sizes=[(16,16),(32,32),(48,48),(64,64),(128,128)])
        else:
            img.save(out)
        return
    except Exception:
        pass
    if shutil.which("magick"):
        _run(["magick", inp, out])
    elif shutil.which("convert"):
        _run(["convert", inp, out])
    else:
        raise RuntimeError("PIL et ImageMagick introuvables. Installez Pillow ou ImageMagick.")


def convert_ffmpeg(inp, out):
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg introuvable. Téléchargez ffmpeg et ajoutez-le au PATH.")
    _run(["ffmpeg", "-i", inp, "-y", out])


def convert_document(inp, out):
    ext_in  = os.path.splitext(inp)[1].lower()
    ext_out = os.path.splitext(out)[1].lower()

    if ext_in in (".txt", ".md") and ext_out == ".html":
        with open(inp, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"<!DOCTYPE html><html><body><pre>{content}</pre></body></html>")
        return

    if ext_in == ".html" and ext_out == ".txt":
        import re
        with open(inp, "r", encoding="utf-8", errors="ignore") as f:
            content = re.sub(r"<[^>]+>", "", f.read())
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
        return

    if ext_in == ".csv" and ext_out == ".txt":
        shutil.copy2(inp, out)
        return

    if shutil.which("soffice"):
        out_dir = os.path.dirname(out)
        ext_lo  = ext_out.lstrip(".")
        _run(["soffice", "--headless", "--convert-to", ext_lo, "--outdir", out_dir, inp])
        base   = os.path.splitext(os.path.basename(inp))[0]
        lo_out = os.path.join(out_dir, f"{base}.{ext_lo}")
        if lo_out != out and os.path.exists(lo_out):
            os.rename(lo_out, out)
        return

    raise RuntimeError("LibreOffice (soffice) introuvable. Installez LibreOffice.")


def convert_archive(inp, out):
    name = os.path.basename(out).lower()
    if name.endswith(".tar.gz"):   ext_out = ".tar.gz"
    elif name.endswith(".tar.bz2"): ext_out = ".tar.bz2"
    elif name.endswith(".tar.xz"):  ext_out = ".tar.xz"
    elif name.endswith(".tbz2"):    ext_out = ".tbz2"
    elif name.endswith(".tgz"):     ext_out = ".tgz"
    else:
        ext_out = os.path.splitext(out)[1].lower()

    if ext_out == ".zip":
        import zipfile
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(inp, os.path.basename(inp))
    elif ext_out in (".tar", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz", ".tbz2"):
        import tarfile
        mode_map = {
            ".tar": "w", ".tgz": "w:gz", ".tar.gz": "w:gz",
            ".tar.bz2": "w:bz2", ".tbz2": "w:bz2", ".tar.xz": "w:xz",
        }
        with tarfile.open(out, mode_map.get(ext_out, "w")) as tf:
            tf.add(inp, arcname=os.path.basename(inp))
    elif ext_out == ".7z":
        try:
            import py7zr
            with py7zr.SevenZipFile(out, "w") as sz:
                sz.write(inp, os.path.basename(inp))
        except ImportError:
            raise RuntimeError("py7zr non installé : pip install py7zr")
    else:
        raise RuntimeError(f"Format archive de sortie non supporté : {ext_out}")


def convert_ebook(inp, out):
    if not shutil.which("ebook-convert"):
        raise RuntimeError(
            "Calibre introuvable.\n"
            "Installez Calibre depuis https://calibre-ebook.com et ajoutez-le au PATH."
        )
    _run(["ebook-convert", inp, out])


def convert_font(inp, out):
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        raise RuntimeError("fonttools non installé : pip install fonttools brotli")
    ext_out = os.path.splitext(out)[1].lower().lstrip(".")
    font = TTFont(inp)
    font.flavor = {"woff": "woff", "woff2": "woff2"}.get(ext_out, None)
    font.save(out)


def convert_vector(inp, out):
    if shutil.which("inkscape"):
        _run(["inkscape", inp, f"--export-filename={out}"])
    elif shutil.which("magick"):
        _run(["magick", inp, out])
    elif shutil.which("convert"):
        _run(["convert", inp, out])
    else:
        raise RuntimeError("Inkscape ou ImageMagick introuvable.")


def convert_cad(inp, out):
    try:
        import ezdxf
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError("ezdxf non installé : pip install ezdxf matplotlib")
    doc = ezdxf.readfile(inp)
    msp = doc.modelspace()
    fig = plt.figure()
    ax  = fig.add_axes([0, 0, 1, 1])
    frontend = Frontend(RenderContext(doc), MatplotlibBackend(ax))
    frontend.draw_layout(msp, finalize=True)
    fig.savefig(out, dpi=200)
    plt.close(fig)


ENGINE_MAP = {
    "imagemagick_or_pil":      convert_image,
    "ffmpeg":                  convert_ffmpeg,
    "libreoffice_or_python":   convert_document,
    "libreoffice":             convert_document,
    "python_tarzip":           convert_archive,
    "calibre":                 convert_ebook,
    "fonttools":               convert_font,
    "inkscape_or_imagemagick": convert_vector,
    "ezdxf":                   convert_cad,
}


# ── Thread ────────────────────────────────────────────────────────────────────

class ConvertThread(QThread):
    done  = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, inp, out, engine):
        super().__init__()
        self.inp, self.out, self.engine = inp, out, engine

    def run(self):
        try:
            ENGINE_MAP[self.engine](self.inp, self.out)
            self.done.emit(self.out)
        except Exception as e:
            self.error.emit(str(e))


# ── Widget ────────────────────────────────────────────────────────────────────

class FileConverterTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang  = lang
        self._input_path = ""
        self._out_dir    = ""
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        cat_row = QHBoxLayout()
        cat_row.addWidget(QLabel("Catégorie :"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(list(CATEGORIES.keys()))
        self.cat_combo.setMinimumHeight(40)
        self.cat_combo.currentTextChanged.connect(self._on_cat_change)
        cat_row.addWidget(self.cat_combo, 1)
        layout.addLayout(cat_row)

        self.note_label = QLabel("")
        self.note_label.setStyleSheet("color: gray; font-size: 11px;")
        self.note_label.setWordWrap(True)
        layout.addWidget(self.note_label)

        src_row = QHBoxLayout()
        self.src_input = QLineEdit()
        self.src_input.setPlaceholderText("Fichier source...")
        self.src_input.setReadOnly(True)
        self.src_input.setMinimumHeight(44)
        self.btn_browse = QPushButton("Parcourir")
        self.btn_browse.setMinimumHeight(44)
        self.btn_browse.clicked.connect(self._browse)
        src_row.addWidget(self.src_input, 1)
        src_row.addWidget(self.btn_browse)
        layout.addLayout(src_row)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Format cible :"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.setMinimumHeight(40)
        fmt_row.addWidget(self.fmt_combo, 1)
        layout.addLayout(fmt_row)

        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Dossier de sortie :"))
        self.out_dir_label = QLabel("Même dossier que la source")
        self.out_dir_label.setStyleSheet("color: gray; font-size: 12px;")
        btn_out = QPushButton("Changer")
        btn_out.setMinimumHeight(36)
        btn_out.clicked.connect(self._choose_out_dir)
        out_row.addWidget(self.out_dir_label, 1)
        out_row.addWidget(btn_out)
        layout.addLayout(out_row)

        self.btn_convert = QPushButton("Convertir")
        self.btn_convert.setMinimumHeight(50)
        self.btn_convert.setObjectName("btn_equal")
        self.btn_convert.clicked.connect(self._convert)
        layout.addWidget(self.btn_convert)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        hint = QLabel("💡 Glissez-déposez un fichier — la catégorie se détecte automatiquement")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        layout.addStretch()
        self._on_cat_change(self.cat_combo.currentText())
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self._load_file(urls[0].toLocalFile())

    def _on_cat_change(self, cat):
        info = CATEGORIES.get(cat, {})
        self.fmt_combo.clear()
        self.fmt_combo.addItems(info.get("formats", []))
        self.note_label.setText(info.get("note", ""))

    def _browse(self):
        cat  = self.cat_combo.currentText()
        exts = CATEGORIES[cat].get("extensions", [])
        filt = f"Fichiers ({' '.join('*' + e for e in exts)});;Tous (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Fichier source", "", filt)
        if path:
            self._load_file(path)

    def _load_file(self, path):
        self._input_path = path
        self.src_input.setText(path)
        ext = os.path.splitext(path)[1].lower()
        for cat, info in CATEGORIES.items():
            if ext in info["extensions"]:
                self.cat_combo.setCurrentText(cat)
                break

    def _choose_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Dossier de sortie")
        if d:
            self._out_dir = d
            self.out_dir_label.setText(d)

    def _convert(self):
        if not self._input_path:
            self.status_label.setText("Sélectionnez un fichier source.")
            return

        cat    = self.cat_combo.currentText()
        fmt    = self.fmt_combo.currentText()
        engine = CATEGORIES[cat]["engine"]
        ext    = f".{fmt.lower()}"
        out_dir = self._out_dir or os.path.dirname(self._input_path)
        base    = os.path.splitext(os.path.basename(self._input_path))[0]
        out_path = os.path.join(out_dir, f"{base}_converted{ext}")

        self.btn_convert.setEnabled(False)
        self.status_label.setText("Conversion en cours...")

        self._thread = ConvertThread(self._input_path, out_path, engine)
        self._thread.done.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_done(self, path):
        self.btn_convert.setEnabled(True)
        self.status_label.setText(f"✅ Fichier converti :\n{path}")

    def _on_error(self, err):
        self.btn_convert.setEnabled(True)
        self.status_label.setText(f"❌ Erreur : {err}")

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang  = lang