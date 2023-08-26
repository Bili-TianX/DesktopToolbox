import typing

from PySide2.QtGui import QFont, QIcon
from PySide2.QtWidgets import QApplication

from .widgets import MainWindow


def main() -> typing.NoReturn:
    _ = QApplication()
    QApplication.setWindowIcon(QIcon('assets/images/icon.svg'))
    QApplication.setFont(QFont('新宋体', 12))

    w = MainWindow()

    w.show()

    exit(QApplication.exec_())
