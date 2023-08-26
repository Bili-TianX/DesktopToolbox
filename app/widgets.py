from PySide2.QtCore import QTimer
from PySide2.QtGui import QCloseEvent, QIcon, Qt
from PySide2.QtWidgets import (QAction, QApplication, QMenu, QSystemTrayIcon,
                               QWidget)

from .modules.core import ModuleContainer
from .modules.countdown import CountdownModule
from .modules.news import NewsModule
from .modules.weather import WeatherModule


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnBottomHint)
        self.setWindowTitle('DesktopToolbox')
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(QApplication.primaryScreen().size())
        self.move(0, 0)

        self.menu = QMenu(self)
        self.exit_action = QAction(
            QIcon('assets/images/exit.svg'), 'Exit', self.menu)
        self.exit_action.triggered.connect(self.onExitAction)
        self.menu.addAction(self.exit_action)

        self.tray = QSystemTrayIcon(QApplication.windowIcon(), self)
        self.tray.show()
        self.tray.setContextMenu(self.menu)

        self.modules: list[ModuleContainer] = [
            ModuleContainer(self, CountdownModule()),
            ModuleContainer(self, NewsModule()),
            ModuleContainer(self, WeatherModule()),
        ]

        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self.tick)
        self.tick_timer.start(1)

    def tick(self):
        for module in self.modules:
            module.tick()

    def onExitAction(self):
        self.close()
        QApplication.exit()

    def closeEvent(self, event: QCloseEvent) -> None:
        for module in self.modules:
            module.save()

        return super().closeEvent(event)
