from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import urllib.request
import json

API_KEY_FILE = "weather_api_key.txt"

WEATHER_ICONS = {
    "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️", "Drizzle": "🌦️",
    "Thunderstorm": "⛈️", "Snow": "❄️", "Mist": "🌫️", "Fog": "🌫️",
    "Haze": "🌫️", "Smoke": "🌫️", "Dust": "🌫️", "Sand": "🌫️",
    "Ash": "🌫️", "Squall": "💨", "Tornado": "🌪️",
}

WIND_DIRS = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSO","SO","OSO","O","ONO","NO","NNO"]


class WeatherThread(QThread):
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, city, api_key):
        super().__init__()
        self.city, self.api_key = city, api_key

    def run(self):
        try:
            from urllib.parse import quote
            url = (f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={quote(self.city)}&appid={self.api_key}&units=metric&lang=fr")
            with urllib.request.urlopen(url, timeout=8) as r:
                data = json.loads(r.read())
            self.done.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class WeatherTool(QWidget):
    def __init__(self, theme, lang):
        super().__init__()
        self.theme = theme
        self.lang = lang
        self._api_key = self._load_key()
        self._build()

    def _load_key(self):
        try:
            with open(API_KEY_FILE) as f:
                return f.read().strip()
        except Exception:
            return ""

    def _save_key(self, key):
        with open(API_KEY_FILE, "w") as f:
            f.write(key)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        # Clé API
        key_row = QHBoxLayout()
        self.key_input = QLineEdit(self._api_key)
        self.key_input.setPlaceholderText("Clé API OpenWeatherMap...")
        self.key_input.setMinimumHeight(38)
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_save = QPushButton("Sauvegarder")
        key_save.setMinimumHeight(38)
        key_save.clicked.connect(lambda: self._save_key(self.key_input.text()))
        key_row.addWidget(QLabel("API Key:"))
        key_row.addWidget(self.key_input, 1)
        key_row.addWidget(key_save)
        layout.addLayout(key_row)

        lbl_hint = QLabel("→ Clé gratuite sur openweathermap.org (onglet API Keys)")
        lbl_hint.setStyleSheet("font-size: 11px; color: gray;")
        layout.addWidget(lbl_hint)

        # Recherche
        search_row = QHBoxLayout()
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText(self.lang["city"])
        self.city_input.setMinimumHeight(44)
        self.city_input.returnPressed.connect(self._search)
        self.btn_search = QPushButton(self.lang["search"])
        self.btn_search.setMinimumHeight(44)
        self.btn_search.clicked.connect(self._search)
        search_row.addWidget(self.city_input, 1)
        search_row.addWidget(self.btn_search)
        layout.addLayout(search_row)

        # Résultat
        self.result_card = QFrame()
        self.result_card.setVisible(False)
        card_layout = QVBoxLayout(self.result_card)
        card_layout.setSpacing(10)

        self.lbl_city_name = QLabel()
        self.lbl_city_name.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.lbl_city_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_icon = QLabel()
        self.lbl_icon.setStyleSheet("font-size: 64px;")
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_temp = QLabel()
        self.lbl_temp.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.lbl_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_desc = QLabel()
        self.lbl_desc.setStyleSheet("font-size: 16px;")
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Détails en grille
        details_grid = QGridLayout()
        details_grid.setSpacing(8)
        self.detail_labels = {}
        details = [
            ("feels_like", "Ressenti"),
            ("humidity", "Humidité"),
            ("wind", "Vent"),
            ("pressure", "Pression"),
            ("visibility", "Visibilité"),
            ("clouds", "Nuages"),
        ]
        for i, (key, name) in enumerate(details):
            row, col = divmod(i, 3)
            frame = QFrame()
            frame.setObjectName("detail_card")
            fl = QVBoxLayout(frame)
            fl.setSpacing(2)
            lbl_name = QLabel(name)
            lbl_name.setStyleSheet("font-size: 11px; color: gray;")
            lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_val = QLabel("—")
            lbl_val.setStyleSheet("font-size: 15px; font-weight: bold;")
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(lbl_name)
            fl.addWidget(lbl_val)
            self.detail_labels[key] = lbl_val
            details_grid.addWidget(frame, row, col)

        card_layout.addWidget(self.lbl_city_name)
        card_layout.addWidget(self.lbl_icon)
        card_layout.addWidget(self.lbl_temp)
        card_layout.addWidget(self.lbl_desc)
        card_layout.addLayout(details_grid)

        layout.addWidget(self.result_card)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addStretch()

    def _search(self):
        city = self.city_input.text().strip()
        key = self.key_input.text().strip()
        if not city or not key:
            self.status_label.setText("Entrez une ville et une clé API.")
            return
        self.status_label.setText("Chargement...")
        self.btn_search.setEnabled(False)
        self._thread = WeatherThread(city, key)
        self._thread.done.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_done(self, data):
        self.btn_search.setEnabled(True)
        self.status_label.clear()
        self.result_card.setVisible(True)

        self.lbl_city_name.setText(f"{data['name']}, {data['sys']['country']}")
        main_weather = data['weather'][0]['main']
        self.lbl_icon.setText(WEATHER_ICONS.get(main_weather, "🌡️"))
        self.lbl_temp.setText(f"{data['main']['temp']:.1f} °C")
        self.lbl_desc.setText(data['weather'][0]['description'].capitalize())

        deg = data['wind']['deg']
        wind_dir = WIND_DIRS[round(deg / 22.5) % 16]
        self.detail_labels["feels_like"].setText(f"{data['main']['feels_like']:.1f} °C")
        self.detail_labels["humidity"].setText(f"{data['main']['humidity']} %")
        self.detail_labels["wind"].setText(f"{data['wind']['speed']:.1f} m/s {wind_dir}")
        self.detail_labels["pressure"].setText(f"{data['main']['pressure']} hPa")
        vis = data.get('visibility', 0)
        self.detail_labels["visibility"].setText(f"{vis/1000:.1f} km")
        self.detail_labels["clouds"].setText(f"{data['clouds']['all']} %")

    def _on_error(self, err):
        self.btn_search.setEnabled(True)
        self.status_label.setText(f"Erreur: {err}")
        self.result_card.setVisible(False)

    def apply_theme(self, theme, lang):
        self.theme = theme
        self.lang = lang