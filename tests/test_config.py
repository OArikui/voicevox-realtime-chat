from voicevox_realtime_chat.config import load_config


def test_load_config_defaults(tmp_path):
    config = load_config(tmp_path / "missing.yaml")
    assert config.title == "VOICEVOX Realtime Chat"
    assert config.voicevox_url == "http://127.0.0.1:50021"
    assert config.voicevox_speaker_id == 1
