from voicevox_realtime_chat.realtime import build_realtime_url, build_session_update


def test_build_realtime_url_encodes_model():
    assert build_realtime_url("gpt-realtime") == (
        "wss://api.openai.com/v1/realtime?model=gpt-realtime"
    )


def test_build_session_update_uses_pcm_and_text_output():
    payload = build_session_update(24000, "日本語で応答してください")
    session = payload["session"]
    assert payload["type"] == "session.update"
    assert session["output_modalities"] == ["text"]
    assert session["audio"]["input"]["format"] == {
        "type": "audio/pcm",
        "rate": 24000,
    }
    assert session["audio"]["input"]["turn_detection"]["type"] == "server_vad"
    assert session["instructions"] == "日本語で応答してください"
