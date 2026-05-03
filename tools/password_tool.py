from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
import random
import string
import math


def password_strength(pwd):
    score = 0
    if len(pwd) >= 8:  score += 1
    if len(pwd) >= 12: score += 1
    if len(pwd) >= 16: score += 1
    if any(c.islower() for c in pwd): score += 1
    if any(c.isupper() for c in pwd): score += 1
    if any(c.isdigit() for c in pwd): score += 1
    if any(c in string.punctuation for c in pwd): score += 1
    return score  # 0-7


STRENGTH_LABELS = ["Très faible", "Très faible", "Faible", "Moyen", "Bon", "Fort", "Très fort", "Excellent"]
STRENGTH_COLORS = ["#ef4444", "#ef4444", "#f97316", "#facc15", "#84cc16", "#22c55e", "#10b981", "#6366f1"]


class PasswordTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._history = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        # ── Résultat ──────────────────────────────────────────────────────────
        result_row = QHBoxLayout()
        self.pwd_display = QLineEdit()
        self.pwd_display.setReadOnly(True)
        self.pwd_display.setMinimumHeight(54)
        self.pwd_display.setStyleSheet("font-size: 18px; font-family: monospace; letter-spacing: 2px;")
        self.pwd_display.setPlaceholderText("Cliquez sur Générer...")

        self.btn_copy = QPushButton("Copier")
        self.btn_copy.setMinimumHeight(54)
        self.btn_copy.setMinimumWidth(90)
        self.btn_copy.clicked.connect(self._copy)

        self.btn_eye = QPushButton("👁")
        self.btn_eye.setMinimumHeight(54)
        self.btn_eye.setMinimumWidth(54)
        self.btn_eye.setCheckable(True)
        self.btn_eye.clicked.connect(self._toggle_visibility)

        result_row.addWidget(self.pwd_display, 1)
        result_row.addWidget(self.btn_eye)
        result_row.addWidget(self.btn_copy)
        layout.addLayout(result_row)

        # Masquer par défaut
        self.pwd_display.setEchoMode(QLineEdit.EchoMode.Password)

        # ── Jauge de force ────────────────────────────────────────────────────
        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximum(7)
        self.strength_bar.setValue(0)
        self.strength_bar.setMinimumHeight(10)
        self.strength_bar.setTextVisible(False)
        layout.addWidget(self.strength_bar)

        self.strength_label = QLabel("")
        self.strength_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.strength_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(self.strength_label)

        # ── Options ───────────────────────────────────────────────────────────
        options_frame = QFrame()
        options_frame.setObjectName("detail_card")
        options_layout = QVBoxLayout(options_frame)
        options_layout.setSpacing(12)

        # Longueur
        len_row = QHBoxLayout()
        len_row.addWidget(QLabel("Longueur :"))
        self.len_label = QLabel("16")
        self.len_label.setStyleSheet("font-weight: bold; min-width: 30px;")
        self.len_slider = QSlider(Qt.Orientation.Horizontal)
        self.len_slider.setRange(4, 64)
        self.len_slider.setValue(16)
        self.len_slider.valueChanged.connect(lambda v: self.len_label.setText(str(v)))
        self.len_slider.valueChanged.connect(self._auto_generate)
        len_row.addWidget(self.len_slider, 1)
        len_row.addWidget(self.len_label)
        options_layout.addLayout(len_row)

        # Cases à cocher
        checks_row = QHBoxLayout()
        self.cb_upper = QCheckBox("Majuscules (A-Z)")
        self.cb_lower = QCheckBox("Minuscules (a-z)")
        self.cb_digits = QCheckBox("Chiffres (0-9)")
        self.cb_symbols = QCheckBox("Symboles (!@#...)")
        self.cb_ambiguous = QCheckBox("Éviter ambigus (0,O,l,I)")

        self.cb_upper.setChecked(True)
        self.cb_lower.setChecked(True)
        self.cb_digits.setChecked(True)
        self.cb_symbols.setChecked(False)
        self.cb_ambiguous.setChecked(False)

        for cb in (self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symbols, self.cb_ambiguous):
            cb.stateChanged.connect(self._auto_generate)

        col1 = QVBoxLayout()
        col1.addWidget(self.cb_upper)
        col1.addWidget(self.cb_lower)
        col2 = QVBoxLayout()
        col2.addWidget(self.cb_digits)
        col2.addWidget(self.cb_symbols)
        col3 = QVBoxLayout()
        col3.addWidget(self.cb_ambiguous)

        checks_row.addLayout(col1)
        checks_row.addLayout(col2)
        checks_row.addLayout(col3)
        options_layout.addLayout(checks_row)

        # Caractères exclus
        excl_row = QHBoxLayout()
        excl_row.addWidget(QLabel("Exclure ces caractères :"))
        self.excl_input = QLineEdit()
        self.excl_input.setPlaceholderText("ex: @#$")
        self.excl_input.setMinimumHeight(36)
        self.excl_input.textChanged.connect(self._auto_generate)
        excl_row.addWidget(self.excl_input, 1)
        options_layout.addLayout(excl_row)

        layout.addWidget(options_frame)

        # ── Bouton générer ────────────────────────────────────────────────────
        self.btn_gen = QPushButton("Générer")
        self.btn_gen.setMinimumHeight(50)
        self.btn_gen.setObjectName("btn_equal")
        self.btn_gen.clicked.connect(self._generate)
        layout.addWidget(self.btn_gen)

        # ── Entropie ──────────────────────────────────────────────────────────
        self.entropy_label = QLabel("")
        self.entropy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.entropy_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.entropy_label)

        # ── Historique ────────────────────────────────────────────────────────
        layout.addWidget(QLabel("Historique de session :"))
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(120)
        self.history_list.itemDoubleClicked.connect(
            lambda item: (
                self.pwd_display.setText(item.text()),
                QApplication.clipboard().setText(item.text())
            )
        )
        layout.addWidget(self.history_list)

        self.copy_status = QLabel("")
        self.copy_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.copy_status)

        layout.addStretch()
        self._generate()

    def _build_charset(self):
        charset = ""
        if self.cb_lower.isChecked():  charset += string.ascii_lowercase
        if self.cb_upper.isChecked():  charset += string.ascii_uppercase
        if self.cb_digits.isChecked(): charset += string.digits
        if self.cb_symbols.isChecked(): charset += string.punctuation

        if self.cb_ambiguous.isChecked():
            for c in "0O1lI|":
                charset = charset.replace(c, "")

        excluded = self.excl_input.text()
        for c in excluded:
            charset = charset.replace(c, "")

        return charset

    def _generate(self):
        charset = self._build_charset()
        if not charset:
            self.pwd_display.setText("")
            self.strength_label.setText("Sélectionnez au moins une option")
            return

        length = self.len_slider.value()

        # Garantir au moins un caractère de chaque catégorie sélectionnée
        required = []
        pool = list(charset)
        if self.cb_lower.isChecked():
            lower = [c for c in string.ascii_lowercase if c in charset]
            if lower: required.append(random.choice(lower))
        if self.cb_upper.isChecked():
            upper = [c for c in string.ascii_uppercase if c in charset]
            if upper: required.append(random.choice(upper))
        if self.cb_digits.isChecked():
            digits = [c for c in string.digits if c in charset]
            if digits: required.append(random.choice(digits))
        if self.cb_symbols.isChecked():
            symbols = [c for c in string.punctuation if c in charset]
            if symbols: required.append(random.choice(symbols))

        remaining = length - len(required)
        pwd_chars = required + [random.choice(pool) for _ in range(max(0, remaining))]
        random.shuffle(pwd_chars)
        pwd = "".join(pwd_chars)

        self.pwd_display.setText(pwd)
        self._update_strength(pwd, charset)

        # Historique
        if pwd and (not self._history or self._history[-1] != pwd):
            self._history.append(pwd)
            masked = pwd[:3] + "•" * (len(pwd) - 3)
            self.history_list.addItem(masked)
            self.history_list.scrollToBottom()

        self.copy_status.clear()

    def _auto_generate(self):
        if self.pwd_display.text():
            self._generate()

    def _update_strength(self, pwd, charset):
        score = password_strength(pwd)
        self.strength_bar.setValue(score)

        color = STRENGTH_COLORS[score]
        label = STRENGTH_LABELS[score]
        self.strength_label.setText(label)
        self.strength_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color};")
        self.strength_bar.setStyleSheet(f"""
            QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}
            QProgressBar {{ border-radius: 4px; background-color: #2a2d45; }}
        """)

        # Entropie
        if len(charset) > 0 and len(pwd) > 0:
            entropy = len(pwd) * math.log2(len(charset))
            self.entropy_label.setText(f"Entropie : {entropy:.1f} bits  |  Charset : {len(charset)} caractères")

    def _copy(self):
        pwd = self.pwd_display.text()
        if pwd:
            QApplication.clipboard().setText(pwd)
            self.copy_status.setText("✅ Copié !")

    def _toggle_visibility(self, checked):
        if checked:
            self.pwd_display.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_eye.setText("🙈")
        else:
            self.pwd_display.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_eye.setText("👁")

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang