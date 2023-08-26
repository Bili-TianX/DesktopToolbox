import sys

from PySide2.QtCore import QProcess
from PySide2.QtWidgets import QApplication


def restart_program():
    from .widgets import MainWindow

    for widget in QApplication.allWidgets():
        if type(widget) == MainWindow:
            widget.close()

    QProcess.startDetached(sys.executable, sys.argv)
    QApplication.exit()
