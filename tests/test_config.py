from voicevox_realtime_chat.config import load_config


def test_load_config_defaults(tmp_path):
    config = load_config(tmp_path / "missing.yaml")
    assert config.title == "VOICEVOX Realtime Chat"
    assert config.voicevox_url == "http://127.0.0.1:50021"
    assert config.voicevox_speaker_id == 1
    assert config.sample_rate == 24000
    assert config.input_device is None
    assert config.output_device is None


def test_load_config_audio_and_instructions(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
openai:
  instructions: "日本語で応答"
audio:
  sample_rate: 16000
  input_device: 2
  output_device: "USB Speakers"
""",
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config.sample_rate == 16000
    assert config.input_device == 2
    assert config.output_device == "USB Speakers"
    assert config.openai_instructions == "日本語で応答"
