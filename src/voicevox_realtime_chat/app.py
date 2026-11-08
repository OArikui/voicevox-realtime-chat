import sys

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from .config import get_openai_api_key, load_config
from .voicevox import VoicevoxClient


class CheckWorker(QObject):
    finished = Signal(str, bool, str)

    def __init__(self, target: str, callback) -> None:
        super().__init__()
        self.target = target
        self.callback = callback

    def run(self) -> None:
        try:
            self.finished.emit(self.target, True, str(self.callback()))
        except Exception as exc:
            self.finished.emit(self.target, False, str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.setWindowTitle(self.config.title)
        self.resize(640, 420)
        self._workers: list[tuple[QThread, CheckWorker]] = []

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("音声会話アプリケーション"))
        self.openai_status = QLabel("OpenAI API: 未確認")
        self.voicevox_status = QLabel("VOICEVOX: 未確認")
        layout.addWidget(self.openai_status)
        layout.addWidget(self.voicevox_status)

        buttons = QHBoxLayout()
        openai_button = QPushButton("OpenAI API 設定確認")
        openai_button.clicked.connect(self.check_openai)
        voicevox_button = QPushButton("VOICEVOX 接続確認")
        voicevox_button.clicked.connect(self.check_voicevox)
        buttons.addWidget(openai_button)
        buttons.addWidget(voicevox_button)
        layout.addLayout(buttons)

        note = QLabel("初期セットアップ版です。会話音声ストリーミングは次の実装段階で追加します。")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()
        self.setCentralWidget(central)

    def _run_check(self, target: str, callback) -> None:
        thread = QThread(self)
        worker = CheckWorker(target, callback)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_check_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._workers.append((thread, worker))
        thread.start()

    def _on_check_finished(self, target: str, success: bool, detail: str) -> None:
        label = self.openai_status if target == "openai" else self.voicevox_status
        label.setText(f"{target.upper()}: {'接続確認済み' if success else '接続失敗'} — {detail}")
        self._workers = [(thread, worker) for thread, worker in self._workers if thread.isRunning()]

    def check_openai(self) -> None:
        if get_openai_api_key():
            self.openai_status.setText("OPENAI: APIキー設定済み（通信テストは次段階で実装）")
        else:
            self.openai_status.setText("OPENAI: APIキー未設定。.env を確認してください。")

    def check_voicevox(self) -> None:
        self.voicevox_status.setText("VOICEVOX: 接続確認中...")
        client = VoicevoxClient(self.config.voicevox_url)
        self._run_check("voicevox", client.get_version)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
