import time
import typing

import requests
from jinja2 import Template
from PySide2.QtCore import QSettings, Qt
from PySide2.QtGui import QContextMenuEvent, QIcon
from PySide2.QtWidgets import (
    QAction,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .config import DEFAULT_WEATHER_UPDATE_DELAY
from .core import BaseModule, DelayValidator

with open("./assets/labels/Weather.html", "r", encoding="utf-8") as f:
    TEMPLATE = Template(f.read())

with open("./assets/labels/CurrentWeather.html", "r", encoding="utf-8") as f:
    CURRENT_WEATHER_TEMPLATE = Template(f.read())


def get_weathers(mode: typing.Literal["base"] | typing.Literal["all"]):
    res = requests.get(
        "https://restapi.amap.com/v3/weather/weatherInfo",
        params={
            "key": "3ab10d97bfed9358845a8b181b6454cf",
            "city": "330782",
            "extensions": mode,
            "output": "json",
        },
    )
    assert res.status_code == 200
    return res.json()


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget, update_delay: float) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")

        self.title_label = QLabel("<h4>Settings</h4>", self)
        self.update_delay_input = QLineEdit(str(update_delay), self)
        self.confirm_button = QPushButton("Confirm", self)
        self.cancel_button = QPushButton("Cancel", self)

        self.title_label.setAlignment(Qt.AlignCenter)
        self.update_delay_input.setValidator(DelayValidator(self.update_delay_input))

        self.form = QFormLayout()
        self.form.addRow("Update Delay", self.update_delay_input)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.confirm_button)
        self.button_layout.addWidget(self.cancel_button)

        self.v = QVBoxLayout(self)
        self.v.addWidget(self.title_label)
        self.v.addLayout(self.form)
        self.v.addLayout(self.button_layout)

        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)


class WeatherModule(BaseModule):
    def __init__(self) -> None:
        super().__init__("Weather")
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setWindowIcon(QIcon("assets/images/settings.svg"))

        self.current_weather_label = QLabel(self)
        self.current_weather_label.setAlignment(Qt.AlignCenter)
        self.update_weather()

        self.v = QVBoxLayout(self)
        self.v.addWidget(self.current_weather_label)

        self.labels = []

        weathers = None
        try:
            weathers = get_weathers("all")["forecasts"][0]["casts"]
        except AssertionError as e:
            self.current_weather_label.setText(f"错误: {e}")
            return

        for weather in weathers:
            label = QLabel(TEMPLATE.render(weather), self)
            label.setAlignment(Qt.AlignCenter)
            self.labels.append(label)
            self.v.addWidget(label)

        self.menu = QMenu(self)

        self.settings_action = QAction(
            QIcon("assets/images/settings.svg"), "Settings", self.menu
        )
        self.settings_action.triggered.connect(self.onSettingsAction)

        self.menu.addActions((self.settings_action,))

    def load(self, settings: QSettings):
        self.UPDATE_DELAY: float = settings.value(
            f"{self.name}/update_delay", DEFAULT_WEATHER_UPDATE_DELAY, float
        )  # type: ignore

    def save(self, settings: QSettings):
        settings.setValue(f"{self.name}/update_delay", self.UPDATE_DELAY)

    def tick(self):
        now = time.time()

        if now - self.last_update_time > self.UPDATE_DELAY:
            self.update_weather()

    def update_weather(self):
        self.last_update_time = time.time()
        try:
            self.current_weather_label.setText(
                CURRENT_WEATHER_TEMPLATE.render(get_weathers("base")["lives"][0])
            )
        except AssertionError as e:
            self.current_weather_label.setText(f"错误: {e}")

    def onSettingsAction(self):
        dialog = SettingsDialog(self, self.UPDATE_DELAY)
        if dialog.exec() == QDialog.Accepted:
            self.UPDATE_DELAY = float(dialog.update_delay_input.text())

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.menu.exec_(event.globalPos())
