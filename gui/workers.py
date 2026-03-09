"""Background worker thread for code comparison."""

from PySide6.QtCore import QThread, Signal


class CompareWorker(QThread):
    """Runs core.api.compare_code() in a background thread."""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, old_path: str, new_path: str,
                 use_ast_diff: bool = False,
                 ignore_formatting: bool = False,
                 excludes: list = None):
        super().__init__()
        self.old_path = old_path
        self.new_path = new_path
        self.use_ast_diff = use_ast_diff
        self.ignore_formatting = ignore_formatting
        self.excludes = excludes or []

    def run(self):
        try:
            from core.api import compare_code
            report = compare_code(
                old_path=self.old_path,
                new_path=self.new_path,
                use_ast_diff=self.use_ast_diff,
                ignore_formatting=self.ignore_formatting,
                excludes=self.excludes if self.excludes else None,
            )
            self.finished.emit(report)
        except Exception as e:
            self.error.emit(str(e))
