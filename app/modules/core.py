import typing

from PySide2.QtCore import QPoint, QSettings
from PySide2.QtGui import (QContextMenuEvent, QFont, QIcon, QMouseEvent,
                           QPainter, QPaintEvent, Qt, QValidator)
from PySide2.QtWidgets import QAction, QFontDialog, QMenu, QVBoxLayout, QWidget

from ..util import restart_program

settings = QSettings('settings.ini', QSettings.IniFormat)


class MyValidator(QValidator):
    def __init__(self, parent) -> None:
        super().__init__(parent)

    def validate(self, input: str, pos: int) -> QValidator.State:
        try:
            assert float(input) > 0
            return QValidator.Acceptable
        except (ValueError, AssertionError):
            return QValidator.Invalid


class BaseModule(QWidget):
    def __init__(self, name: str) -> None:
        super().__init__()

        self.name = name

    def tick(self):
        ...

    def load(self, settings: QSettings):
        ...

    def save(self, settings: QSettings):
        ...


class ModuleContainer(QWidget):
    def __init__(self, parent: typing.Optional[QWidget], module: BaseModule) -> None:
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.dragPosition = QPoint()

        self.module = module
        self.module.setParent(self)

        self.menu = QMenu(self)

        self.font_action = \
            QAction(QIcon('assets/images/font.svg'), 'Font',  self.menu)
        self.menu.addActions((self.font_action, ))

        self.load()
        self.v = QVBoxLayout(self)
        self.v.addSpacing(self.TITLE_BAR_HEIGHT)
        self.v.addWidget(self.module)

        self.font_action.triggered.connect(self.onFontAction)

    def load(self):
        global settings

        self.move(
            settings.value(f'{self.module.name}/pos', QPoint())  # type: ignore
        )
        self.setFont(
            settings.value(f'{self.module.name}/font', QFont())  # type: ignore
        )
        self.TITLE_BAR_HEIGHT = round(self.font().pointSize() * 3) + 10

        self.module.load(settings)

    def save(self):
        global settings

        settings.setValue(
            f'{self.module.name}/pos',
            self.mapToParent(QPoint())
        )
        settings.setValue(
            f'{self.module.name}/font',
            self.font()
        )

        self.module.save(settings)

    def onFontAction(self):
        dialog = QFontDialog(self.font(), self)
        dialog.adjustSize()
        dialog.adjustPosition(self)
        if dialog.exec_() == QFontDialog.Accepted:
            self.setFont(dialog.currentFont())
            restart_program()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.menu.exec_(event.globalPos())
        return super().contextMenuEvent(event)

    def tick(self):
        self.module.tick()
        self.adjustSize()

    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        p.fillRect(0, 0, self.width(), self.TITLE_BAR_HEIGHT,
                   Qt.GlobalColor.cyan)
        p.fillRect(0, self.TITLE_BAR_HEIGHT, self.width(), self.height() - self.TITLE_BAR_HEIGHT,
                   Qt.GlobalColor.white)

        p.drawText(0, 0, self.width(), self.TITLE_BAR_HEIGHT,
                   Qt.AlignCenter, self.module.name)  # type: ignore

        return super().paintEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.dragPosition)

        return super().mouseMoveEvent(event)
