from enum import StrEnum


class SourceKind(StrEnum):
    YOUTUBE_CHANNEL = "youtube_channel"


class ContentItemKind(StrEnum):
    VIDEO = "video"


class TranscriptStatus(StrEnum):
    PENDING = "pending"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class ProcessingStatus(StrEnum):
    INGESTED = "ingested"


class BodyKind(StrEnum):
    TRANSCRIPT = "transcript"
