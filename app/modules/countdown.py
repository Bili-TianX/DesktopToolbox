import sqlite3
import traceback
import typing
from collections import namedtuple
from datetime import datetime

from jinja2 import Template
from PySide2.QtCore import QObject, QSettings
from PySide2.QtGui import QContextMenuEvent, QIcon, Qt
from PySide2.QtWidgets import (
    QAction,
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..util import restart_program
from .config import (
    DAY_IN_SECONDS,
    DB_ADD_COUNTDOWN,
    DB_CREATE_TABLE_COMMAND,
    DB_DELETE_COUNTDOWN,
    DB_FILENAME,
    HOUR_IN_SECONDS,
    MINUTE_IN_SECONDS,
)
from .core import BaseModule, DateValidator


class Countdown(namedtuple("Countdown", ["name", "year", "month", "day"])):
    with open("./assets/labels/Countdown.html", "r", encoding="utf-8") as f:
        TEMPLATE = Template(f.read())

    @property
    def datetime(self):
        if not hasattr(self, "_datetime"):
            self._datetime = datetime(self.year, self.month, self.day, 0, 0, 0)
        return self._datetime

    def get_delta(self) -> typing.Dict[str, typing.Union[int, str]]:
        delta = (self.datetime - datetime.now()).total_seconds()

        days, delta = divmod(delta, DAY_IN_SECONDS)
        hours, delta = divmod(delta, HOUR_IN_SECONDS)
        minutes, delta = divmod(delta, MINUTE_IN_SECONDS)
        seconds, delta = divmod(delta, 1)

        return {
            "name": self.name,
            "days": round(days),
            "hours": round(hours),
            "minutes": round(minutes),
            "seconds": round(seconds),
        }

    def render_template(self):
        return Countdown.TEMPLATE.render(self.get_delta())


class CountdownManager(QObject):
    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.db = sqlite3.connect(DB_FILENAME)
        self.cursor = self.db.cursor()

        self.create_table()

    def create_table(self):
        self.cursor.execute(DB_CREATE_TABLE_COMMAND)

    def add_countdown(self, countdown: Countdown):
        self.cursor.execute(
            DB_ADD_COUNTDOWN
            % (countdown.name, countdown.year, countdown.month, countdown.day)
        )
        self.db.commit()

    def get_countdowns(self):
        self.cursor.execute("SELECT * from countdown")
        for row in self.cursor.fetchall():
            yield Countdown(*row)

    def delete_countdown(self, name: str):
        self.cursor.execute(DB_DELETE_COUNTDOWN % name)

    def close(self):
        self.cursor.close()
        self.db.commit()
        self.db.close()


class AddDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add")
        self.setWindowIcon(QIcon("assets/images/add.svg"))

        self.title_label = QLabel("<h4>Add</h4>", self)

        self.name_input = QLineEdit(self)
        self.year_input = QLineEdit(self)
        self.month_input = QLineEdit(self)
        self.day_input = QLineEdit(self)

        self.confirm_button = QPushButton("Confirm", self)
        self.cancel_button = QPushButton("Cancel", self)

        self.title_label.setAlignment(Qt.AlignCenter)

        self.year_input.setValidator(DateValidator(self.year_input))
        self.month_input.setValidator(DateValidator(self.month_input))
        self.day_input.setValidator(DateValidator(self.day_input))

        self.form = QFormLayout()
        self.form.addRow("Name", self.name_input)
        self.form.addRow("Year", self.year_input)
        self.form.addRow("Month", self.month_input)
        self.form.addRow("Day", self.day_input)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.confirm_button)
        self.button_layout.addWidget(self.cancel_button)

        self.v = QVBoxLayout(self)
        self.v.addWidget(self.title_label)
        self.v.addLayout(self.form)
        self.v.addLayout(self.button_layout)

        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)


class DeleteDialog(QDialog):
    def __init__(self, parent: QWidget, names: tuple[str]) -> None:
        super().__init__(parent)
        self.setWindowTitle("Delete")
        self.setWindowIcon(QIcon("assets/images/delete.svg"))

        self.title_label = QLabel("<h4>Delete</h4>", self)

        self.confirm_button = QPushButton("Confirm", self)
        self.cancel_button = QPushButton("Cancel", self)

        self.title_label.setAlignment(Qt.AlignCenter)

        self.boxes_layout = QVBoxLayout()
        self.boxes: dict[str, QCheckBox] = {}
        for name in names:
            box = QCheckBox(name, self)
            self.boxes[name] = box
            self.boxes_layout.addWidget(box)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.confirm_button)
        self.button_layout.addWidget(self.cancel_button)

        self.v = QVBoxLayout(self)
        self.v.addWidget(self.title_label)
        self.v.addLayout(self.boxes_layout)
        self.v.addLayout(self.button_layout)

        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_selected(self):
        for name, box in self.boxes.items():
            if box.isChecked():
                yield name


class CountdownModule(BaseModule):
    def __init__(self) -> None:
        super().__init__("Countdown")
        self.setContextMenuPolicy(Qt.DefaultContextMenu)

        self.labels: list[QLabel] = []
        self.countdowns: list[Countdown] = []

        self.menu = QMenu(self)

        self.add_action = QAction(QIcon("assets/images/add.svg"), "Add", self.menu)
        self.delete_action = QAction(
            QIcon("assets/images/delete.svg"), "Delete", self.menu
        )
        self.menu.addActions((self.add_action, self.delete_action))

        self.v = QVBoxLayout(self)

        self.add_action.triggered.connect(self.onAddAction)
        self.delete_action.triggered.connect(self.onDeleteAction)

        self.manager = CountdownManager(self)

    def tick(self):
        for i, countdown in enumerate(self.countdowns):
            self.labels[i].setText(countdown.render_template())

    def onAddAction(self):
        dialog = AddDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                countdown = Countdown(
                    dialog.name_input.text(),
                    int(dialog.year_input.text()),
                    int(dialog.month_input.text()),
                    int(dialog.day_input.text()),
                )
                countdown.get_delta()
                self.manager.add_countdown(countdown)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Unable to add countdown:",
                    "".join(traceback.format_exception(e)),
                )
                return
            restart_program()

    def onDeleteAction(self):
        dialog = DeleteDialog(
            self, tuple(countdown.name for countdown in self.countdowns)
        )
        if dialog.exec_() == QDialog.Accepted:
            for selected in dialog.get_selected():
                self.manager.delete_countdown(selected)
            restart_program()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.menu.exec_(event.globalPos())

    def load(self, _: QSettings):
        countdowns = tuple(self.manager.get_countdowns())
        if countdowns:
            for countdown in countdowns:
                label = QLabel(self)
                self.countdowns.append(countdown)
                self.labels.append(label)
                self.v.addWidget(label)
        else:
            self.label = QLabel("暂无倒计时", self)
            self.v.addWidget(self.label)

    def save(self, _: QSettings):
        self.manager.close()
