import json
import re
import time
import typing
from urllib.parse import unquote

import requests
from jinja2 import Template
from PySide2.QtCore import QSettings, Qt
from PySide2.QtGui import QContextMenuEvent, QIcon
from PySide2.QtWidgets import (QAction, QDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenu, QPushButton,
                               QVBoxLayout, QWidget)

from .config import DEFAULT_NEWS_SWITCH_DELAY, DEFAULT_NEWS_UPDATE_DELAY
from .core import BaseModule, MyValidator

with open('./assets/labels/News.html', 'r', encoding='utf-8') as f:
    TEMPLATE = Template(f.read())


def get_news() -> typing.Iterable[dict]:
    res = requests.get('https://top.baidu.com/board?tab=realtime')
    assert res.status_code == 200

    return json.loads(
        unquote(re.findall(r'<!--s-data:(.*?)-->', res.text, re.DOTALL)[0])
    )['data']['cards'][0]['content']


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget, update_delay: float, switch_delay: float) -> None:
        super().__init__(parent)
        self.setWindowTitle('Settings')

        self.title_label = QLabel('<h4>Settings</h4>', self)
        self.update_delay_input = QLineEdit(str(update_delay), self)
        self.switch_delay_input = QLineEdit(str(switch_delay), self)
        self.confirm_button = QPushButton('Confirm', self)
        self.cancel_button = QPushButton('Cancel', self)

        self.title_label.setAlignment(Qt.AlignCenter)
        self.update_delay_input.setValidator(
            MyValidator(self.update_delay_input))
        self.switch_delay_input.setValidator(
            MyValidator(self.switch_delay_input))

        self.form = QFormLayout()
        self.form.addRow('Update Delay', self.update_delay_input)
        self.form.addRow('Switch Delay', self.switch_delay_input)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.confirm_button)
        self.button_layout.addWidget(self.cancel_button)

        self.v = QVBoxLayout(self)
        self.v.addWidget(self.title_label)
        self.v.addLayout(self.form)
        self.v.addLayout(self.button_layout)

        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)


class NewsModule(BaseModule):
    def __init__(self) -> None:
        super().__init__('News')
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setMinimumWidth(480)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)

        self.v = QVBoxLayout(self)
        self.v.addWidget(self.label)

        self.last_switch_time = self.last_update_time = self.idx = 0
        self.labels_content = []
        self.update_news()

        self.menu = QMenu(self)

        self.settings_action = QAction(
            QIcon('assets/images/settings.svg'), 'Settings',  self.menu)
        self.settings_action.triggered.connect(self.onSettingsAction)

        self.menu.addActions((self.settings_action, ))

    def load(self, settings: QSettings):
        self.SWITCH_DELAY: float = settings.value(
            f'{self.name}/switch_delay', DEFAULT_NEWS_SWITCH_DELAY, float)  # type: ignore
        self.UPDATE_DELAY: float = settings.value(
            f'{self.name}/update_delay', DEFAULT_NEWS_UPDATE_DELAY, float)  # type: ignore

    def save(self, settings: QSettings):
        settings.setValue(f'{self.name}/switch_delay', self.SWITCH_DELAY)
        settings.setValue(f'{self.name}/update_delay', self.UPDATE_DELAY)

    def update_news(self):
        self.last_update_time = time.time()

        self.labels_content.clear()
        self.idx = 0
        self.update_success = False

        news = None
        try:
            news = get_news()
        except AssertionError as e:
            self.labels.append(f'错误: {e}')
            return

        for (i, new) in enumerate(news):
            new.update({'i': i, 'total': len(news)})  # type: ignore
            self.labels_content.append(TEMPLATE.render(new))
        self.update_success = True
        self.switch_news(0)

    def switch_news(self, idx: typing.Optional[int] = None):
        self.last_switch_time = time.time()
        self.idx = idx \
            if idx is not None \
            else (self.idx + 1) % len(self.labels_content)
        self.label.setText(self.labels_content[self.idx])

    def tick(self):
        now = time.time()

        if now - self.last_update_time > self.UPDATE_DELAY:
            self.update_news()

        if self.update_success and now - self.last_switch_time > self.SWITCH_DELAY:
            self.switch_news()

    def onSettingsAction(self):
        dialog = SettingsDialog(self, self.UPDATE_DELAY, self.SWITCH_DELAY)
        if dialog.exec() == QDialog.Accepted:
            self.UPDATE_DELAY = float(dialog.update_delay_input.text())
            self.SWITCH_DELAY = float(dialog.switch_delay_input.text())

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.menu.exec_(event.globalPos())
