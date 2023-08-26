import typing
from datetime import datetime

from jinja2 import Template
from PySide2.QtGui import QContextMenuEvent, QIcon, Qt
from PySide2.QtWidgets import QAction, QLabel, QMenu, QVBoxLayout

from .config import DAY_IN_SECONDS, HOUR_IN_SECONDS, MINUTE_IN_SECONDS
from .core import BaseModule

with open('./assets/labels/Countdown.html', 'r', encoding='utf-8') as f:
    TEMPLATE = Template(f.read())


def get_date_delta(name: str, to: datetime) -> typing.Dict[str, typing.Union[int, str]]:
    delta = (to - datetime.now()).total_seconds()

    days, delta = divmod(delta, DAY_IN_SECONDS)
    hours, delta = divmod(delta, HOUR_IN_SECONDS)
    minutes, delta = divmod(delta, MINUTE_IN_SECONDS)
    seconds, delta = divmod(delta, 1)

    return {
        'name': name, 'days': round(days), 'hours': round(hours), 'minutes': round(minutes), 'seconds': round(seconds)
    }


class CountdownModule(BaseModule):
    def __init__(self) -> None:
        super().__init__('Countdown')
        self.setContextMenuPolicy(Qt.DefaultContextMenu)

        self.labels = [
            QLabel(self),
            QLabel(self),
        ]

        self.menu = QMenu(self)

        self.add_action = QAction(
            QIcon('assets/images/add.svg'), 'Add',  self.menu)
        self.menu.addActions((self.add_action, ))

        self.v = QVBoxLayout(self)
        self.v.addWidget(self.labels[0])
        self.v.addWidget(self.labels[1])

        self.add_action.triggered.connect(self.onAddAction)

    def tick(self):
        self.labels[0].setText(TEMPLATE.render(
            get_date_delta('首考', datetime(2024, 1, 6, 0, 0, 0))))
        self.labels[1].setText(TEMPLATE.render(
            get_date_delta('高考', datetime(2024, 6, 7, 0, 0, 0))))

    def onAddAction(self):
        ...

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.menu.exec_(event.globalPos())
