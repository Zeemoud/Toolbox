from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt

CATEGORIES = {
    "Longueur": {
        "Mètre": 1, "Kilomètre": 1000, "Centimètre": 0.01, "Millimètre": 0.001,
        "Micromètre": 1e-6, "Nanomètre": 1e-9, "Mile": 1609.344,
        "Yard": 0.9144, "Pied": 0.3048, "Pouce": 0.0254,
        "Mille marin": 1852, "Année-lumière": 9.461e15,
    },
    "Masse": {
        "Kilogramme": 1, "Gramme": 0.001, "Milligramme": 1e-6,
        "Tonne": 1000, "Livre": 0.453592, "Once": 0.0283495,
        "Carat": 0.0002, "Quintal": 100,
    },
    "Température": {
        "Celsius": "C", "Fahrenheit": "F", "Kelvin": "K",
    },
    "Volume": {
        "Litre": 1, "Millilitre": 0.001, "Centilitre": 0.01,
        "Mètre cube": 1000, "Gallon US": 3.78541, "Gallon UK": 4.54609,
        "Pinte US": 0.473176, "Tasse": 0.236588, "Cuillère à soupe": 0.0147868,
        "Cuillère à café": 0.00492892, "Fluid once": 0.0295735,
    },
    "Superficie": {
        "Mètre carré": 1, "Kilomètre carré": 1e6, "Centimètre carré": 0.0001,
        "Hectare": 10000, "Are": 100, "Acre": 4046.86,
        "Mile carré": 2589988, "Pied carré": 0.092903,
    },
    "Vitesse": {
        "m/s": 1, "km/h": 0.277778, "mph": 0.44704,
        "Nœud": 0.514444, "Mach": 343, "Pied/s": 0.3048,
    },
    "Temps": {
        "Seconde": 1, "Minute": 60, "Heure": 3600, "Jour": 86400,
        "Semaine": 604800, "Mois (30j)": 2592000, "Année": 31557600,
        "Milliseconde": 0.001, "Microseconde": 1e-6,
    },
    "Données": {
        "Bit": 1, "Octet": 8, "Kilooctet": 8192, "Mégaoctet": 8388608,
        "Gigaoctet": 8589934592, "Téraoctet": 8796093022208,
        "Kilobit": 1000, "Mégabit": 1000000, "Gigabit": 1000000000,
    },
    "Pression": {
        "Pascal": 1, "Bar": 100000, "Atmosphère": 101325,
        "PSI": 6894.76, "mmHg": 133.322, "Torr": 133.322,
    },
    "Énergie": {
        "Joule": 1, "Kilojoule": 1000, "Calorie": 4.184,
        "Kilocalorie": 4184, "Wh": 3600, "kWh": 3600000,
        "eV": 1.602e-19, "BTU": 1055.06,
    },
    "Angle": {
        "Degré": 1, "Radian": 57.2958, "Grade": 0.9, "Minute d'arc": 1/60,
    },
}


def convert_temp(value, src, tgt):
    if src == tgt:
        return value
    # vers Celsius
    if src == "Fahrenheit":
        c = (value - 32) * 5/9
    elif src == "Kelvin":
        c = value - 273.15
    else:
        c = value
    # depuis Celsius
    if tgt == "Fahrenheit":
        return c * 9/5 + 32
    elif tgt == "Kelvin":
        return c + 273.15
    return c


class ConverterTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        # Catégorie
        cat_row = QHBoxLayout()
        cat_row.addWidget(QLabel(self.lang["category"]))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(list(CATEGORIES.keys()))
        self.cat_combo.setMinimumHeight(40)
        self.cat_combo.currentTextChanged.connect(self._on_cat_change)
        cat_row.addWidget(self.cat_combo, 1)
        layout.addLayout(cat_row)

        # Valeur + unités
        conv_layout = QGridLayout()
        conv_layout.setSpacing(10)

        conv_layout.addWidget(QLabel(self.lang["value"]), 0, 0)
        self.val_input = QLineEdit("1")
        self.val_input.setMinimumHeight(44)
        self.val_input.textChanged.connect(self._convert)
        conv_layout.addWidget(self.val_input, 0, 1, 1, 2)

        conv_layout.addWidget(QLabel(self.lang["from_unit"]), 1, 0)
        self.from_combo = QComboBox()
        self.from_combo.setMinimumHeight(40)
        self.from_combo.currentTextChanged.connect(self._convert)
        conv_layout.addWidget(self.from_combo, 1, 1)

        swap_btn = QPushButton("⇄")
        swap_btn.setFixedSize(44, 40)
        swap_btn.clicked.connect(self._swap)
        conv_layout.addWidget(swap_btn, 1, 2)

        conv_layout.addWidget(QLabel(self.lang["to_unit"]), 2, 0)
        self.to_combo = QComboBox()
        self.to_combo.setMinimumHeight(40)
        self.to_combo.currentTextChanged.connect(self._convert)
        conv_layout.addWidget(self.to_combo, 2, 1, 1, 2)

        layout.addLayout(conv_layout)

        # Résultat
        self.result_label = QLabel("—")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 36px; font-weight: bold; padding: 20px;")
        layout.addWidget(self.result_label)

        self.formula_label = QLabel("")
        self.formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formula_label.setStyleSheet("font-size: 13px; color: gray;")
        layout.addWidget(self.formula_label)

        # Tableau de conversions rapides
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Unité", "Valeur"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMaximumHeight(200)
        layout.addWidget(self.table)

        layout.addStretch()
        self._on_cat_change(self.cat_combo.currentText())

    def _on_cat_change(self, cat):
        units = list(CATEGORIES[cat].keys())
        self.from_combo.blockSignals(True)
        self.to_combo.blockSignals(True)
        self.from_combo.clear()
        self.to_combo.clear()
        self.from_combo.addItems(units)
        self.to_combo.addItems(units)
        if len(units) > 1:
            self.to_combo.setCurrentIndex(1)
        self.from_combo.blockSignals(False)
        self.to_combo.blockSignals(False)
        self._convert()

    def _swap(self):
        f, t = self.from_combo.currentText(), self.to_combo.currentText()
        self.from_combo.setCurrentText(t)
        self.to_combo.setCurrentText(f)

    def _convert(self):
        try:
            value = float(self.val_input.text().replace(",", "."))
        except ValueError:
            self.result_label.setText("—")
            return

        cat = self.cat_combo.currentText()
        src = self.from_combo.currentText()
        tgt = self.to_combo.currentText()
        units = CATEGORIES[cat]

        if cat == "Température":
            result = convert_temp(value, src, tgt)
        else:
            src_factor = units.get(src, 1)
            tgt_factor = units.get(tgt, 1)
            result = value * src_factor / tgt_factor

        # Format intelligent
        if abs(result) >= 1e9 or (abs(result) < 1e-4 and result != 0):
            txt = f"{result:.4e}"
        elif result == int(result):
            txt = f"{int(result):,}".replace(",", " ")
        else:
            txt = f"{result:.6g}"

        self.result_label.setText(f"{txt} {tgt}")
        self.formula_label.setText(f"{value} {src}  =  {txt} {tgt}")

        # Tableau
        self._fill_table(value, cat, src, units)

    def _fill_table(self, value, cat, src, units):
        self.table.setRowCount(0)
        if cat == "Température":
            rows = [("Celsius", convert_temp(value, src, "Celsius")),
                    ("Fahrenheit", convert_temp(value, src, "Fahrenheit")),
                    ("Kelvin", convert_temp(value, src, "Kelvin"))]
        else:
            src_f = units[src]
            rows = []
            for u, f in units.items():
                if u == src:
                    continue
                rows.append((u, value * src_f / f))

        for unit, val in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(unit))
            if abs(val) >= 1e9 or (abs(val) < 1e-4 and val != 0):
                v_txt = f"{val:.4e}"
            elif val == int(val):
                v_txt = f"{int(val):,}".replace(",", " ")
            else:
                v_txt = f"{val:.6g}"
            self.table.setItem(r, 1, QTableWidgetItem(v_txt))

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang