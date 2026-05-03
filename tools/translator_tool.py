from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal


LANGUAGES = {
    "Français": "fr", "English": "en", "Español": "es", "Deutsch": "de",
    "Italiano": "it", "Português": "pt", "Русский": "ru", "日本語": "ja",
    "中文": "zh-CN", "العربية": "ar", "한국어": "ko", "Nederlands": "nl",
    "Polski": "pl", "Türkçe": "tr", "Svenska": "sv",
}


class TranslateThread(QThread):
    done = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, text, src, tgt):
        super().__init__()
        self.text, self.src, self.tgt = text, src, tgt

    def run(self):
        try:
            from deep_translator import GoogleTranslator
            result = GoogleTranslator(source=self.src, target=self.tgt).translate(self.text)
            self.done.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class TranslatorTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        # Sélection langues
        row = QHBoxLayout()
        self.src_combo = QComboBox()
        self.src_combo.addItems(list(LANGUAGES.keys()))
        self.src_combo.setCurrentText("Français")
        self.src_combo.setMinimumHeight(40)

        swap_btn = QPushButton("⇄")
        swap_btn.setFixedSize(44, 40)
        swap_btn.clicked.connect(self._swap)

        self.tgt_combo = QComboBox()
        self.tgt_combo.addItems(list(LANGUAGES.keys()))
        self.tgt_combo.setCurrentText("English")
        self.tgt_combo.setMinimumHeight(40)

        row.addWidget(QLabel(self.lang["from_lang"]))
        row.addWidget(self.src_combo, 1)
        row.addWidget(swap_btn)
        row.addWidget(QLabel(self.lang["to_lang"]))
        row.addWidget(self.tgt_combo, 1)
        layout.addLayout(row)

        # Zones texte
        texts = QHBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(self.lang["text_to_trans"])
        self.input_text.setMinimumHeight(200)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText(self.lang["result"] + "...")
        self.output_text.setMinimumHeight(200)

        texts.addWidget(self.input_text)
        texts.addWidget(self.output_text)
        layout.addLayout(texts)

        # Boutons
        btns = QHBoxLayout()
        self.btn_translate = QPushButton(self.lang["translate"])
        self.btn_translate.setMinimumHeight(44)
        self.btn_translate.clicked.connect(self._translate)

        self.btn_copy = QPushButton(self.lang["copy"])
        self.btn_copy.setMinimumHeight(44)
        self.btn_copy.clicked.connect(self._copy)

        self.btn_clear = QPushButton(self.lang["clear"])
        self.btn_clear.setMinimumHeight(44)
        self.btn_clear.clicked.connect(self._clear)

        btns.addWidget(self.btn_translate, 2)
        btns.addWidget(self.btn_copy)
        btns.addWidget(self.btn_clear)
        layout.addLayout(btns)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _swap(self):
        s, t = self.src_combo.currentText(), self.tgt_combo.currentText()
        self.src_combo.setCurrentText(t)
        self.tgt_combo.setCurrentText(s)

    def _translate(self):
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        src = LANGUAGES[self.src_combo.currentText()]
        tgt = LANGUAGES[self.tgt_combo.currentText()]
        self.status_label.setText("Traduction en cours...")
        self.btn_translate.setEnabled(False)
        self._thread = TranslateThread(text, src, tgt)
        self._thread.done.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_done(self, result):
        self.output_text.setPlainText(result)
        self.status_label.setText("")
        self.btn_translate.setEnabled(True)

    def _on_error(self, err):
        self.status_label.setText(f"Erreur : {err}")
        self.btn_translate.setEnabled(True)

    def _copy(self):
        text = self.output_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText(self.lang["copied"])

    def _clear(self):
        self.input_text.clear()
        self.output_text.clear()
        self.status_label.clear()

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang