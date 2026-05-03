from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import math


class CalculatorTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._expr = ""
        self._history = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)

        # Tabs basique / avancée
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_basic(), self.lang["basic_calc"])
        self.tabs.addTab(self._build_advanced(), self.lang["advanced_calc"])
        layout.addWidget(self.tabs)

    # ── Calculatrice Basique ──────────────────────────────────────────────────
    def _build_basic(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)

        self.display = QLineEdit("0")
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setMinimumHeight(70)
        self.display.setStyleSheet("font-size: 32px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.display)

        self.sub_display = QLabel("")
        self.sub_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.sub_display.setStyleSheet("font-size: 13px; color: gray; padding-right: 4px;")
        layout.addWidget(self.sub_display)

        btns = [
            ["C", "±", "%", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            ["0", ".", "⌫", "="],
        ]

        grid = QGridLayout()
        grid.setSpacing(8)
        for r, row in enumerate(btns):
            for c, label in enumerate(row):
                btn = QPushButton(label)
                btn.setMinimumHeight(64)
                btn.setMinimumWidth(64)
                if label == "=":
                    btn.setObjectName("btn_equal")
                elif label in ("÷", "×", "−", "+", "%"):
                    btn.setObjectName("btn_op")
                elif label in ("C", "±", "⌫"):
                    btn.setObjectName("btn_func")
                btn.clicked.connect(lambda _, l=label: self._on_btn(l))
                grid.addWidget(btn, r, c)

        layout.addLayout(grid)

        # Historique
        layout.addWidget(QLabel(self.lang["history"]))
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(100)
        self.history_list.itemDoubleClicked.connect(
            lambda item: self.display.setText(item.text().split("=")[-1].strip()))
        layout.addWidget(self.history_list)

        return w

    def _on_btn(self, label):
        current = self.display.text()

        if label == "C":
            self._expr = ""
            self.display.setText("0")
            self.sub_display.clear()
        elif label == "⌫":
            self._expr = self._expr[:-1]
            self.display.setText(self._expr or "0")
        elif label == "±":
            try:
                val = float(self._expr or "0")
                self._expr = str(-val)
                self.display.setText(self._expr)
            except Exception:
                pass
        elif label == "%":
            try:
                val = float(self._expr or "0") / 100
                self._expr = str(val)
                self.display.setText(self._expr)
            except Exception:
                pass
        elif label == "=":
            try:
                expr = self._expr.replace("÷", "/").replace("×", "*").replace("−", "-")
                result = eval(expr)
                if result == int(result):
                    result_str = str(int(result))
                else:
                    result_str = f"{result:.10g}"
                self.sub_display.setText(f"{self._expr} =")
                entry = f"{self._expr} = {result_str}"
                self._history.append(entry)
                self.history_list.addItem(entry)
                self.history_list.scrollToBottom()
                self._expr = result_str
                self.display.setText(result_str)
            except Exception:
                self.display.setText("Erreur")
                self._expr = ""
        else:
            if current == "0" and label not in (".", "÷", "×", "−", "+"):
                self._expr = label
            else:
                self._expr += label
            self.display.setText(self._expr)

    # ── Calculatrice Avancée ──────────────────────────────────────────────────
    def _build_advanced(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        self.adv_input = QLineEdit()
        self.adv_input.setPlaceholderText("Expression... ex: sin(pi/2) + sqrt(16)")
        self.adv_input.setMinimumHeight(50)
        self.adv_input.setStyleSheet("font-size: 16px; padding: 8px;")
        self.adv_input.returnPressed.connect(self._eval_advanced)
        layout.addWidget(self.adv_input)

        self.adv_result = QLabel("—")
        self.adv_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.adv_result.setStyleSheet("font-size: 32px; font-weight: bold; padding: 16px;")
        layout.addWidget(self.adv_result)

        btn_row = QHBoxLayout()
        calc_btn = QPushButton(self.lang["calculate"])
        calc_btn.setMinimumHeight(44)
        calc_btn.clicked.connect(self._eval_advanced)
        clear_btn = QPushButton(self.lang["clear"])
        clear_btn.setMinimumHeight(44)
        clear_btn.clicked.connect(lambda: (self.adv_input.clear(), self.adv_result.setText("—")))
        btn_row.addWidget(calc_btn)
        btn_row.addWidget(clear_btn)
        layout.addLayout(btn_row)

        # Boutons fonctions
        funcs = [
            ["sin", "cos", "tan", "asin", "acos", "atan"],
            ["sqrt", "log", "log10", "exp", "abs", "factorial"],
            ["ceil", "floor", "π", "e", "^", "!"],
        ]
        for row in funcs:
            row_layout = QHBoxLayout()
            for f in row:
                b = QPushButton(f)
                b.setMinimumHeight(36)
                b.clicked.connect(lambda _, fn=f: self._insert_func(fn))
                row_layout.addWidget(b)
            layout.addLayout(row_layout)

        # Aide
        help_text = QLabel(
            "Fonctions: sin, cos, tan, sqrt, log, exp, abs, ceil, floor, factorial\n"
            "Constantes: pi, e  |  Puissance: 2**8  |  Exemple: sqrt(2**8 + sin(pi/4))"
        )
        help_text.setStyleSheet("color: gray; font-size: 11px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        layout.addStretch()
        return w

    def _insert_func(self, fn):
        specials = {"π": "pi", "e": "e", "^": "**", "!": "factorial("}
        insert = specials.get(fn, fn + "(")
        cursor_pos = self.adv_input.cursorPosition()
        text = self.adv_input.text()
        self.adv_input.setText(text[:cursor_pos] + insert + text[cursor_pos:])

    def _eval_advanced(self):
        expr = self.adv_input.text().strip()
        if not expr:
            return
        safe_env = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        safe_env["pi"] = math.pi
        safe_env["e"] = math.e
        try:
            result = eval(expr.replace("^", "**"), {"__builtins__": {}}, safe_env)
            if isinstance(result, float) and result == int(result):
                self.adv_result.setText(str(int(result)))
            else:
                self.adv_result.setText(f"{result:.10g}")
        except Exception as ex:
            self.adv_result.setText(f"Erreur: {ex}")

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang
        self.tabs.setTabText(0, lang["basic_calc"])
        self.tabs.setTabText(1, lang["advanced_calc"])