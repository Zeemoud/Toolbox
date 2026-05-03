from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
import base64
import urllib.parse
import hashlib
import html

MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', ' ': '/',
}
MORSE_REVERSE = {v: k for k, v in MORSE_CODE.items()}

def to_morse(text):
    return ' '.join(MORSE_CODE.get(c.upper(), '?') for c in text)

def from_morse(text):
    return ''.join(MORSE_REVERSE.get(c, '?') for c in text.split(' '))

def to_binary(text):
    return ' '.join(format(ord(c), '08b') for c in text)

def from_binary(text):
    try:
        return ''.join(chr(int(b, 2)) for b in text.split())
    except Exception:
        return "Erreur de décodage"

def to_hex(text):
    return text.encode('utf-8').hex()

def from_hex(text):
    try:
        return bytes.fromhex(text.replace(' ', '')).decode('utf-8')
    except Exception:
        return "Erreur de décodage"

def rot13(text):
    result = []
    for c in text:
        if 'a' <= c <= 'z':
            result.append(chr((ord(c) - ord('a') + 13) % 26 + ord('a')))
        elif 'A' <= c <= 'Z':
            result.append(chr((ord(c) - ord('A') + 13) % 26 + ord('A')))
        else:
            result.append(c)
    return ''.join(result)

MODES = {
    "Base64":        (lambda t: base64.b64encode(t.encode()).decode(),
                      lambda t: base64.b64decode(t.encode()).decode()),
    "URL Encode":    (urllib.parse.quote, urllib.parse.unquote),
    "HTML Entities": (html.escape, html.unescape),
    "Hexadécimal":   (to_hex, from_hex),
    "Binaire":       (to_binary, from_binary),
    "Morse":         (to_morse, from_morse),
    "ROT13":         (rot13, rot13),
    "MD5 (hash)":    (lambda t: hashlib.md5(t.encode()).hexdigest(), None),
    "SHA256 (hash)": (lambda t: hashlib.sha256(t.encode()).hexdigest(), None),
    "SHA512 (hash)": (lambda t: hashlib.sha512(t.encode()).hexdigest(), None),
}


class EncoderTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode :"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(list(MODES.keys()))
        self.mode_combo.setMinimumHeight(40)
        self.mode_combo.currentTextChanged.connect(self._on_mode_change)
        mode_row.addWidget(self.mode_combo, 1)
        layout.addLayout(mode_row)

        self.mode_hint = QLabel("")
        self.mode_hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.mode_hint)

        texts = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("Entrée :"))
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Texte à encoder / décoder...")
        self.input_text.setMinimumHeight(180)
        left.addWidget(self.input_text)

        right = QVBoxLayout()
        right.addWidget(QLabel("Résultat :"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(180)
        right.addWidget(self.output_text)

        texts.addLayout(left)
        texts.addLayout(right)
        layout.addLayout(texts)

        btns = QHBoxLayout()
        self.btn_encode = QPushButton("Encoder →")
        self.btn_encode.setMinimumHeight(44)
        self.btn_encode.setObjectName("btn_equal")
        self.btn_encode.clicked.connect(self._encode)

        self.btn_decode = QPushButton("← Décoder")
        self.btn_decode.setMinimumHeight(44)
        self.btn_decode.clicked.connect(self._decode)

        btn_swap = QPushButton("⇄ Inverser")
        btn_swap.setMinimumHeight(44)
        btn_swap.clicked.connect(self._swap)

        btn_copy = QPushButton("Copier")
        btn_copy.setMinimumHeight(44)
        btn_copy.clicked.connect(self._copy)

        btn_clear = QPushButton("Effacer")
        btn_clear.setMinimumHeight(44)
        btn_clear.clicked.connect(self._clear)

        for b in (self.btn_encode, self.btn_decode, btn_swap, btn_copy, btn_clear):
            btns.addWidget(b)
        layout.addLayout(btns)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)
        layout.addStretch()
        self._on_mode_change(self.mode_combo.currentText())

    def _on_mode_change(self, mode):
        hints = {
            "MD5 (hash)":    "Hash unidirectionnel — décodage impossible",
            "SHA256 (hash)": "Hash unidirectionnel — décodage impossible",
            "SHA512 (hash)": "Hash unidirectionnel — décodage impossible",
            "ROT13":         "ROT13 est son propre inverse — encode = décode",
            "Morse":         "Séparez les lettres par des espaces, les mots par /",
            "Binaire":       "Groupes de 8 bits séparés par des espaces",
        }
        self.mode_hint.setText(hints.get(mode, ""))
        self.btn_decode.setEnabled("hash" not in mode.lower())

    def _encode(self):
        text = self.input_text.toPlainText()
        enc_fn, _ = MODES[self.mode_combo.currentText()]
        try:
            self.output_text.setPlainText(enc_fn(text))
            self.status.clear()
        except Exception as e:
            self.status.setText(f"Erreur : {e}")

    def _decode(self):
        text = self.input_text.toPlainText()
        _, dec_fn = MODES[self.mode_combo.currentText()]
        if dec_fn is None:
            self.status.setText("Décodage impossible pour ce mode.")
            return
        try:
            self.output_text.setPlainText(dec_fn(text))
            self.status.clear()
        except Exception as e:
            self.status.setText(f"Erreur : {e}")

    def _swap(self):
        a, b = self.input_text.toPlainText(), self.output_text.toPlainText()
        self.input_text.setPlainText(b)
        self.output_text.setPlainText(a)

    def _copy(self):
        text = self.output_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status.setText("Copié !")

    def _clear(self):
        self.input_text.clear()
        self.output_text.clear()
        self.status.clear()

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang