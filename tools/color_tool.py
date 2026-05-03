from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient, QPixmap
import colorsys
import random


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"

def rgb_to_hsl(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return round(h*360), round(s*100), round(l*100)

def hsl_to_rgb(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h/360, l/100, s/100)
    return round(r*255), round(g*255), round(b*255)

def rgb_to_cmyk(r, g, b):
    if r == g == b == 0:
        return 0, 0, 0, 100
    r_, g_, b_ = r/255, g/255, b/255
    k = 1 - max(r_, g_, b_)
    c = (1 - r_ - k) / (1 - k)
    m = (1 - g_ - k) / (1 - k)
    y = (1 - b_ - k) / (1 - k)
    return round(c*100), round(m*100), round(y*100), round(k*100)

def contrast_color(r, g, b):
    luminance = 0.299*r + 0.587*g + 0.114*b
    return "#000000" if luminance > 128 else "#ffffff"

def generate_palette(r, g, b, mode):
    h, s, l = rgb_to_hsl(r, g, b)
    if mode == "Complémentaire":
        colors = [rgb_to_hex(r, g, b), rgb_to_hex(*hsl_to_rgb((h+180)%360, s, l))]
    elif mode == "Triadique":
        colors = [rgb_to_hex(*hsl_to_rgb((h+i)%360, s, l)) for i in (0, 120, 240)]
    elif mode == "Analogique":
        colors = [rgb_to_hex(*hsl_to_rgb((h+i)%360, s, l)) for i in (-30, -15, 0, 15, 30)]
    elif mode == "Teintes":
        colors = [rgb_to_hex(*hsl_to_rgb(h, s, min(100, l+i))) for i in (-30, -15, 0, 15, 30)]
    elif mode == "Monochromatique":
        colors = [rgb_to_hex(*hsl_to_rgb(h, max(0, s+i), l)) for i in (-40, -20, 0, 20, 40)]
    else:
        colors = [rgb_to_hex(r, g, b)]
    return colors


class ColorSwatch(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, hex_color="#ffffff", size=60):
        super().__init__()
        self._hex = hex_color
        self.setFixedSize(size, size)
        self._update()

    def set_color(self, hex_color):
        self._hex = hex_color
        self._update()

    def _update(self):
        self.setStyleSheet(f"""
            background-color: {self._hex};
            border-radius: 8px;
            border: 2px solid rgba(0,0,0,0.2);
        """)
        self.setToolTip(self._hex)

    def mousePressEvent(self, event):
        QApplication.clipboard().setText(self._hex)
        self.clicked.emit(self._hex)


class ColorTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._r, self._g, self._b = 108, 90, 247  # violet par défaut
        self._build()
        self._update_all()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # ── Panneau gauche ────────────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(12)

        # Grande swatch
        self.main_swatch = QLabel()
        self.main_swatch.setMinimumHeight(120)
        self.main_swatch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_swatch.setStyleSheet("border-radius: 12px; font-size: 16px; font-weight: bold;")
        left.addWidget(self.main_swatch)

        # Bouton picker natif
        self.btn_picker = QPushButton("Choisir une couleur...")
        self.btn_picker.setMinimumHeight(44)
        self.btn_picker.clicked.connect(self._open_picker)
        left.addWidget(self.btn_picker)

        # HEX input
        hex_row = QHBoxLayout()
        hex_row.addWidget(QLabel("HEX :"))
        self.hex_input = QLineEdit()
        self.hex_input.setMinimumHeight(40)
        self.hex_input.setPlaceholderText("#6C5AF7")
        self.hex_input.editingFinished.connect(self._on_hex_input)
        hex_row.addWidget(self.hex_input, 1)
        btn_copy_hex = QPushButton("Copier")
        btn_copy_hex.setMinimumHeight(40)
        btn_copy_hex.clicked.connect(lambda: (
            QApplication.clipboard().setText(self.hex_input.text()),
        ))
        hex_row.addWidget(btn_copy_hex)
        left.addLayout(hex_row)

        # Sliders RGB
        self.sliders = {}
        for channel, color in [("R", "#ef4444"), ("G", "#22c55e"), ("B", "#3b82f6")]:
            row = QHBoxLayout()
            lbl = QLabel(f"{channel}:")
            lbl.setFixedWidth(20)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 255)
            slider.setStyleSheet(f"QSlider::handle {{ background: {color}; }}")
            val_lbl = QLabel("0")
            val_lbl.setFixedWidth(30)
            slider.valueChanged.connect(lambda v, c=channel, vl=val_lbl: self._on_slider(c, v, vl))
            row.addWidget(lbl)
            row.addWidget(slider, 1)
            row.addWidget(val_lbl)
            left.addLayout(row)
            self.sliders[channel] = (slider, val_lbl)

        # Bouton aléatoire
        btn_random = QPushButton("🎲 Couleur aléatoire")
        btn_random.setMinimumHeight(40)
        btn_random.clicked.connect(self._random_color)
        left.addWidget(btn_random)

        # Infos couleur
        info_frame = QFrame()
        info_frame.setObjectName("detail_card")
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(6)

        self.info_labels = {}
        infos = [("HEX", 0, 0), ("RGB", 0, 2), ("HSL", 1, 0), ("CMYK", 1, 2)]
        for name, row, col in infos:
            info_layout.addWidget(QLabel(f"{name}:"), row, col)
            lbl = QLabel("—")
            lbl.setStyleSheet("font-weight: bold; font-size: 11px;")
            info_layout.addWidget(lbl, row, col+1)
            self.info_labels[name] = lbl

        left.addWidget(info_frame)
        left.addStretch()

        # ── Panneau droite : palette ──────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(12)

        right.addWidget(QLabel("Palette :"))
        self.palette_combo = QComboBox()
        self.palette_combo.addItems(["Complémentaire", "Triadique", "Analogique", "Teintes", "Monochromatique"])
        self.palette_combo.setMinimumHeight(40)
        self.palette_combo.currentTextChanged.connect(self._update_palette)
        right.addWidget(self.palette_combo)

        self.palette_swatches = QHBoxLayout()
        self.palette_swatches.setSpacing(8)
        self._swatch_widgets = []
        for _ in range(5):
            sw = ColorSwatch()
            sw.clicked.connect(lambda h: self.status.setText(f"Copié : {h}"))
            self._swatch_widgets.append(sw)
            self.palette_swatches.addWidget(sw)
        right.addLayout(self.palette_swatches)

        right.addWidget(QLabel("Export CSS :"))
        self.css_output = QTextEdit()
        self.css_output.setReadOnly(True)
        self.css_output.setMaximumHeight(120)
        right.addWidget(self.css_output)

        btn_copy_css = QPushButton("Copier le CSS")
        btn_copy_css.setMinimumHeight(40)
        btn_copy_css.clicked.connect(lambda: QApplication.clipboard().setText(self.css_output.toPlainText()))
        right.addWidget(btn_copy_css)

        # Dégradé
        right.addWidget(QLabel("Aperçu dégradé :"))
        self.gradient_label = QLabel()
        self.gradient_label.setMinimumHeight(60)
        self.gradient_label.setStyleSheet("border-radius: 8px;")
        right.addWidget(self.gradient_label)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("color: gray; font-size: 11px;")
        right.addWidget(self.status)
        right.addStretch()

        layout.addLayout(left, 1)
        layout.addLayout(right, 1)

    def _on_slider(self, channel, value, val_lbl):
        val_lbl.setText(str(value))
        if channel == "R": self._r = value
        elif channel == "G": self._g = value
        elif channel == "B": self._b = value
        self._update_all(skip_sliders=True)

    def _on_hex_input(self):
        hex_val = self.hex_input.text().strip()
        if not hex_val.startswith("#"):
            hex_val = "#" + hex_val
        try:
            r, g, b = hex_to_rgb(hex_val)
            self._r, self._g, self._b = r, g, b
            self._update_all()
        except Exception:
            pass

    def _open_picker(self):
        color = QColorDialog.getColor(
            QColor(self._r, self._g, self._b), self, "Choisir une couleur"
        )
        if color.isValid():
            self._r, self._g, self._b = color.red(), color.green(), color.blue()
            self._update_all()

    def _random_color(self):
        self._r = random.randint(0, 255)
        self._g = random.randint(0, 255)
        self._b = random.randint(0, 255)
        self._update_all()

    def _update_all(self, skip_sliders=False):
        r, g, b = self._r, self._g, self._b
        hex_val = rgb_to_hex(r, g, b)
        text_color = contrast_color(r, g, b)

        self.main_swatch.setStyleSheet(
            f"background-color: {hex_val}; border-radius: 12px; "
            f"color: {text_color}; font-size: 18px; font-weight: bold;"
        )
        self.main_swatch.setText(hex_val)

        self.hex_input.setText(hex_val)

        if not skip_sliders:
            for ch, (slider, lbl) in self.sliders.items():
                val = {"R": r, "G": g, "B": b}[ch]
                slider.blockSignals(True)
                slider.setValue(val)
                slider.blockSignals(False)
                lbl.setText(str(val))

        h, s, l = rgb_to_hsl(r, g, b)
        c, m, y, k = rgb_to_cmyk(r, g, b)
        self.info_labels["HEX"].setText(hex_val)
        self.info_labels["RGB"].setText(f"rgb({r}, {g}, {b})")
        self.info_labels["HSL"].setText(f"hsl({h}, {s}%, {l}%)")
        self.info_labels["CMYK"].setText(f"C:{c} M:{m} Y:{y} K:{k}")

        self._update_palette()
        self._update_gradient()
        self._update_css(hex_val, r, g, b, h, s, l)

    def _update_palette(self):
        mode = self.palette_combo.currentText()
        colors = generate_palette(self._r, self._g, self._b, mode)
        for i, sw in enumerate(self._swatch_widgets):
            if i < len(colors):
                sw.set_color(colors[i])
                sw.setVisible(True)
            else:
                sw.setVisible(False)

    def _update_gradient(self):
        r, g, b = self._r, self._g, self._b
        h, s, l = rgb_to_hsl(r, g, b)
        comp = rgb_to_hex(*hsl_to_rgb((h+180)%360, s, l))
        self.gradient_label.setStyleSheet(
            f"border-radius: 8px; "
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {rgb_to_hex(r,g,b)}, stop:1 {comp});"
        )

    def _update_css(self, hex_val, r, g, b, h, s, l):
        css = (
            f":root {{\n"
            f"  --color-primary: {hex_val};\n"
            f"  --color-primary-rgb: {r}, {g}, {b};\n"
            f"  --color-primary-hsl: {h}, {s}%, {l}%;\n"
            f"  --color-complement: {rgb_to_hex(*hsl_to_rgb((h+180)%360, s, l))};\n"
            f"  --color-light: {rgb_to_hex(*hsl_to_rgb(h, s, min(90, l+20)))};\n"
            f"  --color-dark: {rgb_to_hex(*hsl_to_rgb(h, s, max(10, l-20)))};\n"
            f"}}"
        )
        self.css_output.setPlainText(css)

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang