from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor
import qrcode
from io import BytesIO
from PIL.ImageQt import ImageQt
import os


class QRTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._qr_img = None
        self._build()

    def _build(self):
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(30, 30, 30, 30)
        self.layout_.setSpacing(16)

        # Input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.lang["qr_input"])
        self.input_field.setMinimumHeight(44)
        self.layout_.addWidget(self.input_field)

        # Options row
        row = QHBoxLayout()
        self.size_label = QLabel("Taille:")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(100, 600)
        self.size_spin.setValue(300)
        self.size_spin.setSuffix(" px")
        self.size_spin.setMinimumHeight(36)

        self.color_label = QLabel("Couleur:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Noir", "Violet", "Teal", "Rouge"])
        self.color_combo.setMinimumHeight(36)

        row.addWidget(self.size_label)
        row.addWidget(self.size_spin)
        row.addSpacing(20)
        row.addWidget(self.color_label)
        row.addWidget(self.color_combo)
        row.addStretch()
        self.layout_.addLayout(row)

        # Bouton générer
        self.btn_gen = QPushButton(self.lang["generate"])
        self.btn_gen.setMinimumHeight(44)
        self.btn_gen.clicked.connect(self._generate)
        self.layout_.addWidget(self.btn_gen)

        # Affichage QR
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setMinimumHeight(300)
        self.layout_.addWidget(self.qr_label)

        # Bouton save
        self.btn_save = QPushButton(self.lang["save"])
        self.btn_save.setMinimumHeight(40)
        self.btn_save.clicked.connect(self._save)
        self.btn_save.setEnabled(False)
        self.layout_.addWidget(self.btn_save)

        self.layout_.addStretch()

    def _generate(self):
        text = self.input_field.text().strip()
        if not text:
            return

        colors = {"Noir": "#000000", "Violet": "#6c5ae7", "Teal": "#0d9488", "Rouge": "#dc2626"}
        fill = colors.get(self.color_combo.currentText(), "#000000")
        size = self.size_spin.value()

        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        self._qr_img = qr.make_image(fill_color=fill, back_color="white")

        buf = BytesIO()
        self._qr_img.save(buf, format="PNG")
        buf.seek(0)

        qt_img = QImage()
        qt_img.loadFromData(buf.read())
        pix = QPixmap.fromImage(qt_img).scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.qr_label.setPixmap(pix)
        self.btn_save.setEnabled(True)

    def _save(self):
        if self._qr_img is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer", "qrcode.png", "PNG (*.png)")
        if path:
            self._qr_img.save(path)

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang
        self.input_field.setPlaceholderText(lang["qr_input"])
        self.btn_gen.setText(lang["generate"])
        self.btn_save.setText(lang["save"])