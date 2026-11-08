from __future__ import annotations

import sys
import threading

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .config import get_openai_api_key, load_config
from .realtime import RealtimeClient
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


class ConversationWorker(QObject):
    status = Signal(str)
    text = Signal(str)
    error = Signal(str)
    completed = Signal()

    def __init__(self, client: RealtimeClient) -> None:
        super().__init__()
        self.client = client
        self.stop_event = threading.Event()

    def run(self) -> None:
        try:
            self.client.run(self.stop_event, self.status.emit, self.text.emit)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.completed.emit()

    def stop(self) -> None:
        self.stop_event.set()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.setWindowTitle(self.config.title)
        self.resize(720, 520)
        self._workers: list[tuple[QThread, CheckWorker]] = []
        self._conversation_thread: QThread | None = None
        self._conversation_worker: ConversationWorker | None = None

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("VOICEVOX Realtime Chat"))

        self.openai_status = QLabel("OpenAI API: 未確認")
        self.voicevox_status = QLabel("VOICEVOX: 未確認")
        self.conversation_status = QLabel("会話: 停止中")
        layout.addWidget(self.openai_status)
        layout.addWidget(self.voicevox_status)
        layout.addWidget(self.conversation_status)

        buttons = QHBoxLayout()
        openai_button = QPushButton("OpenAI API 設定確認")
        openai_button.clicked.connect(self.check_openai)
        voicevox_button = QPushButton("VOICEVOX 接続確認")
        voicevox_button.clicked.connect(self.check_voicevox)
        self.start_button = QPushButton("会話開始")
        self.start_button.clicked.connect(self.start_conversation)
        self.stop_button = QPushButton("会話停止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_conversation)
        for button in (
            openai_button,
            voicevox_button,
            self.start_button,
            self.stop_button,
        ):
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self.transcript = QPlainTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText("会話内容がここに表示されます。")
        layout.addWidget(self.transcript)
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
        label.setText(
            f"{target.upper()}: {'接続確認済み' if success else '接続失敗'} — {detail}"
        )
        self._workers = [
            (thread, worker) for thread, worker in self._workers if thread.isRunning()
        ]

    def check_openai(self) -> None:
        if get_openai_api_key():
            self.openai_status.setText("OPENAI: APIキー設定済み")
        else:
            self.openai_status.setText("OPENAI: APIキー未設定。.env を確認してください。")

    def check_voicevox(self) -> None:
        self.voicevox_status.setText("VOICEVOX: 接続確認中...")
        client = VoicevoxClient(self.config.voicevox_url)
        self._run_check("voicevox", client.get_version)

    def start_conversation(self) -> None:
        api_key = get_openai_api_key()
        if not api_key:
            self.conversation_status.setText(
                "会話: OPENAI_API_KEY が未設定です。.env を確認してください。"
            )
            return
        if self._conversation_thread is not None:
            return

        voicevox = VoicevoxClient(self.config.voicevox_url)
        client = RealtimeClient(
            api_key=api_key,
            model=self.config.openai_model,
            voicevox=voicevox,
            speaker_id=self.config.voicevox_speaker_id,
            speed_scale=self.config.voicevox_speed,
            sample_rate=self.config.sample_rate,
            input_device=self.config.input_device,
            output_device=self.config.output_device,
            instructions=self.config.openai_instructions,
        )
        thread = QThread(self)
        worker = ConversationWorker(client)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.status.connect(self._on_conversation_status)
        worker.text.connect(self._append_transcript)
        worker.error.connect(self._on_conversation_error)
        worker.completed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        thread.finished.connect(self._on_conversation_finished)
        thread.finished.connect(thread.deleteLater)
        self._conversation_thread = thread
        self._conversation_worker = worker
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.conversation_status.setText("会話: 起動中...")
        thread.start()

    def stop_conversation(self) -> None:
        if self._conversation_worker is not None:
            self._conversation_worker.stop()
            self.stop_button.setEnabled(False)
            self.conversation_status.setText("会話: 停止しています...")

    def _on_conversation_status(self, message: str) -> None:
        self.conversation_status.setText(f"会話: {message}")

    def _append_transcript(self, message: str) -> None:
        self.transcript.appendPlainText(message)

    def _on_conversation_error(self, message: str) -> None:
        self.conversation_status.setText(f"会話エラー: {message}")
        self.transcript.appendPlainText(f"[エラー] {message}")

    def _on_conversation_finished(self) -> None:
        self._conversation_thread = None
        self._conversation_worker = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if not self.conversation_status.text().startswith("会話エラー:"):
            self.conversation_status.setText("会話: 停止中")

    def closeEvent(self, event) -> None:
        self.stop_conversation()
        if self._conversation_thread is not None:
            self._conversation_thread.quit()
            self._conversation_thread.wait(3000)
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
