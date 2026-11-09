from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .config import load_config
from .voicevox import VoicevoxClient


class CheckWorker(QObject):
    finished = Signal(bool, str)

    def __init__(self, callback) -> None:
        super().__init__()
        self.callback = callback

    def run(self) -> None:
        try:
            self.finished.emit(True, str(self.callback()))
        except Exception as exc:
            self.finished.emit(False, str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.setWindowTitle(self.config.title)
        self.resize(560, 300)
        self._check_thread: QThread | None = None
        self._check_worker: CheckWorker | None = None

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("VOICEVOX Realtime Chat"))

        self.conversation_status = QLabel(
            "会話機能: 未定（AI会話エンジンを選定していません）"
        )
        self.conversation_status.setWordWrap(True)
        layout.addWidget(self.conversation_status)

        self.voicevox_status = QLabel("VOICEVOX: 未確認")
        layout.addWidget(self.voicevox_status)

        self.check_button = QPushButton("VOICEVOX 接続確認")
        self.check_button.clicked.connect(self.check_voicevox)
        layout.addWidget(self.check_button)

        self.setCentralWidget(central)

    def check_voicevox(self) -> None:
        if self._check_thread is not None:
            return

        self.check_button.setEnabled(False)
        self.voicevox_status.setText("VOICEVOX: 接続確認中...")
        client = VoicevoxClient(self.config.voicevox_url)

        thread = QThread(self)
        worker = CheckWorker(client.get_version)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_check_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_check_thread_finished)
        thread.finished.connect(thread.deleteLater)

        self._check_thread = thread
        self._check_worker = worker
        thread.start()

    def _on_check_finished(self, success: bool, detail: str) -> None:
        if success:
            self.voicevox_status.setText(f"VOICEVOX: 接続済み (version {detail})")
        else:
            self.voicevox_status.setText(f"VOICEVOX: 接続失敗 — {detail}")

    def _on_check_thread_finished(self) -> None:
        self._check_thread = None
        self._check_worker = None
        self.check_button.setEnabled(True)

    def closeEvent(self, event) -> None:
        if self._check_thread is not None:
            self._check_thread.quit()
            self._check_thread.wait(3000)
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
