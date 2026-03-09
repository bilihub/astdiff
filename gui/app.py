"""StdDiff GUI application entry point."""

import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

import FluentUI

from gui.backend import Backend


def run():
    # QApplication (not QGuiApplication) is needed for QFileDialog
    app = QApplication(sys.argv)
    app.setOrganizationName("StdDiff")
    app.setApplicationName("StdDiff")

    engine = QQmlApplicationEngine()

    # Register FluentUI QML components
    FluentUI.init(engine)

    # Create and inject backend
    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    # Load main QML
    qml_dir = os.path.join(os.path.dirname(__file__), "qml")
    qml_file = os.path.join(qml_dir, "App.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        print("Error: Failed to load QML file:", qml_file)
        sys.exit(-1)

    sys.exit(app.exec())
