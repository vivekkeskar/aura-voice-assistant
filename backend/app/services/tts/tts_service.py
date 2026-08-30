import base64
import re
from abc import ABC, abstractmethod
from typing import AsyncGenerator

import edge_tts
import httpx

from app.config.settings import settings
from app.utils.logger import logger


class BaseTTSService(ABC):
    @abstractmethod
    async def stream_tts_audio_base64(self, text: str) -> AsyncGenerator[str, None]:
        """Generate streaming TTS audio chunks for input text, yielding base64 strings."""
        pass


class EdgeTTSService(BaseTTSService):
    def __init__(self, voice: str = "en-US-AvaNeural"):
        self.voice = voice

    async def stream_tts_audio_base64(self, text: str) -> AsyncGenerator[str, None]:
        if not text.strip():
            return

        # Split long text into natural sentences to stream complete, valid MP3 audio buffers per sentence
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not sentences:
            sentences = [text.strip()]

        for sentence in sentences:
            try:
                logger.info(f"[EdgeTTS] Synthesizing sentence ({len(sentence)} chars): '{sentence[:30]}...'")
                communicate = edge_tts.Communicate(text=sentence, voice=self.voice)
                sentence_audio = bytearray()

                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_bytes = chunk["data"]
                        if audio_bytes:
                            sentence_audio.extend(audio_bytes)

                if sentence_audio:
                    b64_audio = base64.b64encode(sentence_audio).decode("utf-8")
                    yield b64_audio

            except Exception as e:
                logger.error(f"[EdgeTTS] Sentence synthesis error: {e}")


class ElevenLabsTTSService(BaseTTSService):
    def __init__(self, api_key: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        self.api_key = api_key
        self.voice_id = voice_id

    async def stream_tts_audio_base64(self, text: str) -> AsyncGenerator[str, None]:
        if not text.strip():
            return
        if not self.api_key:
            logger.warning("[ElevenLabs] API key missing; falling back to EdgeTTS.")
            edge_fallback = EdgeTTSService()
            async for chunk in edge_fallback.stream_tts_audio_base64(text):
                yield chunk
            return

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
            headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    audio_buf = bytearray()
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            audio_buf.extend(chunk)
                    if audio_buf:
                        yield base64.b64encode(audio_buf).decode("utf-8")
        except Exception as e:
            logger.error(f"[ElevenLabs] Streaming error: {e}")
            edge_fallback = EdgeTTSService()
            async for chunk in edge_fallback.stream_tts_audio_base64(text):
                yield chunk


def get_tts_service() -> BaseTTSService:
    provider = getattr(settings, "TTS_PROVIDER", "edge").lower()
    if provider == "elevenlabs" and settings.ELEVENLABS_API_KEY:
        return ElevenLabsTTSService(settings.ELEVENLABS_API_KEY)
    return EdgeTTSService()


tts_service = get_tts_service()
