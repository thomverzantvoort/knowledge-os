from enum import StrEnum


class SubscriptionKind(StrEnum):
    YOUTUBE_CHANNEL = "youtube_channel"


class ContentKind(StrEnum):
    VIDEO = "video"


class BodyStatus(StrEnum):
    PENDING = "pending"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class ProcessingStatus(StrEnum):
    INGESTED = "ingested"
    FAILED = "failed"


class UserStatus(StrEnum):
    UNREAD = "unread"
    INTERESTED = "interested"
    DISMISSED = "dismissed"


class BodyKind(StrEnum):
    TRANSCRIPT = "transcript"


class OutputLanguage(StrEnum):
    EN = "en"
    NL = "nl"
    CONTENT = "content"
