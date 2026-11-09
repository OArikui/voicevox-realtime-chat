from voicevox_realtime_chat.config import load_config


def test_load_config_defaults(tmp_path):
    config = load_config(tmp_path / "missing.yaml")
    assert config.title == "VOICEVOX Realtime Chat"
    assert config.voicevox_url == "http://127.0.0.1:50021"
    assert config.voicevox_speaker_id == 1
    assert config.voicevox_speed == 1.0


def test_load_config_voicevox_options(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
app:
  title: "Test Voice App"
voicevox:
  base_url: "http://localhost:50021/"
  speaker_id: 3
  speed_scale: 1.2
""",
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.title == "Test Voice App"
    assert config.voicevox_url == "http://localhost:50021"
    assert config.voicevox_speaker_id == 3
    assert config.voicevox_speed == 1.2


def test_load_config_ignores_legacy_openai_and_audio_options(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
openai:
  model: "legacy-model"
audio:
  sample_rate: 16000
voicevox:
  base_url: "http://127.0.0.1:50021"
""",
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.voicevox_url == "http://127.0.0.1:50021"
