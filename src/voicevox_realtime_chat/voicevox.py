import httpx


class VoicevoxClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_version(self) -> str:
        response = httpx.get(f"{self.base_url}/version", timeout=self.timeout)
        response.raise_for_status()
        return response.text.strip().strip('"')

    def get_speakers(self) -> list[dict]:
        response = httpx.get(f"{self.base_url}/speakers", timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []

    def synthesize(self, text: str, speaker_id: int, speed_scale: float = 1.0) -> bytes:
        if not text.strip():
            raise ValueError("Text to synthesize must not be empty.")
        query_response = httpx.post(
            f"{self.base_url}/audio_query",
            params={"text": text, "speaker": speaker_id},
            timeout=self.timeout,
        )
        query_response.raise_for_status()
        query = query_response.json()
        query["speedScale"] = speed_scale
        audio_response = httpx.post(
            f"{self.base_url}/synthesis",
            params={"speaker": speaker_id},
            json=query,
            timeout=max(self.timeout, 30.0),
        )
        audio_response.raise_for_status()
        return audio_response.content
