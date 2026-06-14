"""Abstract base class and data types for ASR engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Segment:
    """A single timed segment of transcribed speech."""

    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    """Full transcription result returned by an ASR engine."""

    text: str
    segments: list[Segment] = field(default_factory=list)
    language: str = "zh"
    engine_name: str = ""
    model_name: str = ""
    audio_duration: float = 0.0
    processing_time: float = 0.0


class ASREngine(ABC):
    """Interface that every ASR backend must implement."""

    @abstractmethod
    def transcribe(
        self, audio_path: str, language: str = "auto"
    ) -> TranscriptResult:
        """Transcribe an audio file and return a ``TranscriptResult``."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return ``True`` if all runtime dependencies are importable."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name, e.g. ``'sensevoice'``."""

    @property
    @abstractmethod
    def priority(self) -> int:
        """Selection priority — higher is preferred.

        Conventions: SenseVoice = 100, faster-whisper = 50.
        """
