from __future__ import annotations

import asyncio
import base64
import io
import json
import threading
from collections.abc import Callable
from urllib.parse import urlencode

import websockets

from .voicevox import VoicevoxClient

StatusCallback = Callable[[str], None]
TextCallback = Callable[[str], None]


def build_realtime_url(model: str) -> str:
    return "wss://api.openai.com/v1/realtime?" + urlencode({"model": model})


def build_session_update(sample_rate: int, instructions: str) -> dict:
    return {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "instructions": instructions,
            "output_modalities": ["text"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcm", "rate": sample_rate},
                    "transcription": {"model": "gpt-4o-mini-transcribe"},
                    "turn_detection": {
                        "type": "server_vad",
                        "create_response": True,
                        "interrupt_response": True,
                    },
                }
            },
        },
    }


class RealtimeClient:
    """Realtime microphone client that delegates spoken responses to VOICEVOX."""

    def __init__(
        self,
        api_key: str,
        model: str,
        voicevox: VoicevoxClient,
        speaker_id: int,
        speed_scale: float,
        sample_rate: int = 24000,
        input_device: int | str | None = None,
        output_device: int | str | None = None,
        instructions: str = "あなたは親切で簡潔な日本語の音声アシスタントです。",
    ) -> None:
        if sample_rate != 24000:
            raise ValueError("OpenAI Realtime PCM input currently requires 24000 Hz.")
        self.api_key = api_key
        self.model = model
        self.voicevox = voicevox
        self.speaker_id = speaker_id
        self.speed_scale = speed_scale
        self.sample_rate = sample_rate
        self.input_device = input_device
        self.output_device = output_device
        self.instructions = instructions
        self._speaking = threading.Event()

    def run(
        self,
        stop_event: threading.Event,
        on_status: StatusCallback,
        on_text: TextCallback,
    ) -> None:
        asyncio.run(self._run(stop_event, on_status, on_text))

    async def _run(
        self,
        stop_event: threading.Event,
        on_status: StatusCallback,
        on_text: TextCallback,
    ) -> None:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY が設定されていません。")

        import sounddevice as sd

        headers = {"Authorization": f"Bearer {self.api_key}"}
        on_status("OpenAI Realtime API に接続しています...")
        async with websockets.connect(
            build_realtime_url(self.model),
            additional_headers=headers,
            ping_interval=20,
            open_timeout=15,
            close_timeout=5,
            max_size=8 * 1024 * 1024,
        ) as websocket:
            await websocket.send(
                json.dumps(
                    build_session_update(self.sample_rate, self.instructions),
                    ensure_ascii=False,
                )
            )
            await self._wait_for_session(websocket)
            on_status("接続しました。マイクで話してください。")

            chunk_frames = max(1, self.sample_rate // 10)
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=chunk_frames,
                device=self.input_device,
                channels=1,
                dtype="int16",
            ) as microphone:
                sender = asyncio.create_task(
                    self._send_audio(websocket, microphone, stop_event)
                )
                receiver = asyncio.create_task(
                    self._receive_events(websocket, stop_event, on_status, on_text)
                )
                done, pending = await asyncio.wait(
                    {sender, receiver}, return_when=asyncio.FIRST_COMPLETED
                )
                if sender in done:
                    await websocket.close()
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                for task in done:
                    task.result()

        on_status("会話を終了しました。")

    async def _wait_for_session(self, websocket) -> None:
        while True:
            raw_event = await asyncio.wait_for(websocket.recv(), timeout=15)
            event = json.loads(raw_event)
            event_type = event.get("type")
            if event_type == "session.updated":
                return
            if event_type == "error":
                message = event.get("error", {}).get("message", "Unknown API error")
                raise RuntimeError(f"Realtime API: {message}")

    async def _send_audio(self, websocket, microphone, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            audio, overflowed = await asyncio.to_thread(
                microphone.read, max(1, self.sample_rate // 10)
            )
            if overflowed or self._speaking.is_set():
                continue
            payload = {
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(audio).decode("ascii"),
            }
            await websocket.send(json.dumps(payload))

    async def _receive_events(
        self,
        websocket,
        stop_event: threading.Event,
        on_status: StatusCallback,
        on_text: TextCallback,
    ) -> None:
        response_text = ""
        async for raw_event in websocket:
            if stop_event.is_set():
                return
            event = json.loads(raw_event)
            event_type = event.get("type", "")

            if event_type == "error":
                message = event.get("error", {}).get("message", "Unknown API error")
                on_status(f"APIエラー: {message}")
                continue
            if event_type == "input_audio_buffer.speech_started":
                on_status("音声を認識しています...")
            elif event_type == "conversation.item.input_audio_transcription.completed":
                transcript = event.get("transcript", "").strip()
                if transcript:
                    on_text(f"あなた: {transcript}")
            elif event_type == "response.output_text.delta":
                response_text += event.get("delta", "")
            elif event_type == "response.output_text.done":
                completed_text = (event.get("text") or response_text).strip()
                response_text = ""
                if completed_text:
                    on_text(f"AI: {completed_text}")
                    on_status("VOICEVOXで読み上げています...")
                    await asyncio.to_thread(self._speak, completed_text)
                    on_status("接続中です。続けて話してください。")
            elif event_type == "response.done":
                response_text = ""

    def _speak(self, text: str) -> None:
        import sounddevice as sd
        import soundfile as sf

        self._speaking.set()
        try:
            wav_data = self.voicevox.synthesize(
                text, self.speaker_id, self.speed_scale
            )
            audio, sample_rate = sf.read(io.BytesIO(wav_data), dtype="float32")
            sd.play(audio, samplerate=sample_rate, device=self.output_device)
            sd.wait()
        finally:
            self._speaking.clear()
