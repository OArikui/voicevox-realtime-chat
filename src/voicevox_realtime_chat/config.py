from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    title: str
    voicevox_url: str
    voicevox_speaker_id: int
    voicevox_speed: float


def load_config(path: Path | str = "config.yaml") -> AppConfig:
    config_path = Path(path)
    raw: dict[str, Any] = {}
    if config_path.is_file():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            raw = loaded

    app = raw.get("app", {})
    voicevox = raw.get("voicevox", {})
    return AppConfig(
        title=str(app.get("title", "VOICEVOX Realtime Chat")),
        voicevox_url=str(
            voicevox.get("base_url", "http://127.0.0.1:50021")
        ).rstrip("/"),
        voicevox_speaker_id=int(voicevox.get("speaker_id", 1)),
        voicevox_speed=float(voicevox.get("speed_scale", 1.0)),
    )
