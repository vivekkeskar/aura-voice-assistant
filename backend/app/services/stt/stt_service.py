from typing import Callable

from app.config.settings import settings
from app.utils.logger import logger


class STTService:
    """
    Primary STT Service using Deepgram Live Streaming WebSocket API.
    Processes incoming PCM 16-bit Mono @ 16kHz audio chunks.
    """

    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self.sample_rate = 16000
        self.encoding = "linear16"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "your_deepgram_api_key_here")

    async def connect_deepgram_stream(self, on_transcript_callback: Callable[[str, bool], None]):
        """
        Establishes live WebSocket stream with Deepgram API.
        Receives linear16 16kHz audio bytes, emitting (transcript, is_final).
        """
        if not self.is_configured():
            logger.info("Deepgram API key not provided; using client-side WebSpeech fallback.")
            return None

        try:
            from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

            deepgram = DeepgramClient(self.api_key)

            dg_connection = deepgram.listen.websocket.v("1")

            def on_message(self_dg, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                if len(sentence) == 0:
                    return
                is_final = result.is_final
                on_transcript_callback(sentence, is_final)

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            options = LiveOptions(
                model="nova-2",
                punctuate=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True,
            )

            if await dg_connection.start(options):
                logger.info("Deepgram WebSocket STT stream started successfully.")
                return dg_connection
        except Exception as e:
            logger.error(f"Failed to start Deepgram WebSocket connection: {e}")
            return None


stt_service = STTService()
