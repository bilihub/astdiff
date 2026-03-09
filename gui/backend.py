"""Python backend object exposed to QML."""

import json
from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl
from PySide6.QtWidgets import QFileDialog

from gui.workers import CompareWorker


class Backend(QObject):
    """Bridge between QML UI and the core diff engine."""

    compareFinished = Signal()
    compareError = Signal(str)
    runningChanged = Signal()
    reportChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._report = {}
        self._worker = None

    # ── Properties ──────────────────────────────────────────

    def _get_running(self):
        return self._running

    def _set_running(self, v):
        if self._running != v:
            self._running = v
            self.runningChanged.emit()

    running = Property(bool, _get_running, notify=runningChanged)

    def _get_report(self):
        return self._report

    report = Property("QVariant", _get_report, notify=reportChanged)

    # ── Slots ───────────────────────────────────────────────

    @Slot(str, str, bool, bool, str)
    def compare(self, old_path: str, new_path: str,
                use_ast_diff: bool, ignore_formatting: bool,
                excludes_str: str):
        """Start a comparison in a background thread."""
        if self._running:
            return

        self._set_running(True)

        excludes = [e.strip() for e in excludes_str.split(",") if e.strip()] if excludes_str else []

        self._worker = CompareWorker(
            old_path=old_path,
            new_path=new_path,
            use_ast_diff=use_ast_diff,
            ignore_formatting=ignore_formatting,
            excludes=excludes,
        )
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    @Slot(result=str)
    def chooseFolder(self):
        """Open a native folder picker and return the selected path."""
        path = QFileDialog.getExistingDirectory(None, "选择目录")
        return path if path else ""

    @Slot(result=str)
    def chooseFile(self):
        """Open a native file picker and return the selected path."""
        path, _ = QFileDialog.getOpenFileName(
            None, "选择文件",
            "", "Source Files (*.c *.cpp *.h *.hpp *.cc *.cxx *.hxx *.xml);;All Files (*)"
        )
        return path if path else ""

    @Slot(result=str)
    def getReportJson(self):
        """Return the current report as a JSON string for QML consumption."""
        return json.dumps(self._report, ensure_ascii=False, default=str)

    # ── Internal ────────────────────────────────────────────

    def _on_finished(self, report: dict):
        self._report = report
        self.reportChanged.emit()
        self._set_running(False)
        self.compareFinished.emit()

    def _on_error(self, message: str):
        self._set_running(False)
        self.compareError.emit(message)
