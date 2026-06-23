import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import feedparser
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi, YouTubeTranscriptApiException

logger = logging.getLogger(__name__)

YOUTUBE_CHANNEL_RSS_URL = (
    "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
)
YOUTUBE_VIDEO_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def youtube_thumbnail_url(video_id: str) -> str:
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


def get_channel_metadata(channel_id: str) -> tuple[str | None, str | None]:
    feed = _fetch_channel_feed(channel_id)
    feed_info = feed.feed
    title = feed_info.get("title")
    url = feed_info.get("link")
    return title, url


def _fetch_channel_feed(channel_id: str) -> feedparser.FeedParserDict:
    rss_url = YOUTUBE_CHANNEL_RSS_URL.format(channel_id=channel_id)
    feed = feedparser.parse(rss_url)

    if feed.bozo and not feed.entries and not feed.feed.get("title"):
        message = "RSS feed parse failed"
        if feed.bozo_exception:
            message = f"{message}: {feed.bozo_exception}"
        raise ValueError(message)

    return feed


def _extract_video_id(entry: feedparser.FeedParserDict) -> str | None:
    video_id = getattr(entry, "yt_videoid", None)
    if video_id and YOUTUBE_VIDEO_ID_PATTERN.match(video_id):
        return video_id
    return _video_id_from_url(entry.link)


def _video_id_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname and "youtu.be" in parsed.hostname:
        candidate = parsed.path.lstrip("/").split("/")[0]
        if YOUTUBE_VIDEO_ID_PATTERN.match(candidate):
            return candidate

    if parsed.path.startswith("/shorts/"):
        candidate = parsed.path.split("/")[2]
        if YOUTUBE_VIDEO_ID_PATTERN.match(candidate):
            return candidate

    query_id = parse_qs(parsed.query).get("v", [None])[0]
    if query_id and YOUTUBE_VIDEO_ID_PATTERN.match(query_id):
        return query_id

    return None


def _parse_entry_published(entry: feedparser.FeedParserDict) -> datetime:
    published_parsed = entry.get("published_parsed")
    if published_parsed:
        return datetime(
            published_parsed.tm_year,
            published_parsed.tm_mon,
            published_parsed.tm_mday,
            published_parsed.tm_hour,
            published_parsed.tm_min,
            published_parsed.tm_sec,
            tzinfo=timezone.utc,
        )

    return datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%S%z")


class TranscriptSnippet(BaseModel):
    text: str
    start: float
    duration: float


class Transcript(BaseModel):
    text: str
    language: str
    language_code: str
    is_generated: bool
    snippets: list[TranscriptSnippet]


class VideoData(BaseModel):
    video_id: str
    title: str
    description: str
    published_at: datetime
    url: str
    channel_title: str
    thumbnail_url: str
    transcript: Transcript | None = None
    transcript_error: str | None = None


class YouTubeScraper:
    def __init__(
        self,
        transcript_languages: list[str] | None = None,
        exclude_shorts: bool = True,
    ):
        self.transcript_languages = transcript_languages or ["en", "nl"]
        self.exclude_shorts = exclude_shorts
        self.ytt_api = YouTubeTranscriptApi()

    def get_channel_videos(self, channel_id: str, hours: int = 168) -> list[VideoData]:
        feed = _fetch_channel_feed(channel_id)

        if not feed.entries:
            logger.warning("RSS feed returned no entries for channel %s", channel_id)
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        videos: list[VideoData] = []

        for entry in feed.entries:
            published = _parse_entry_published(entry)
            if published < cutoff:
                continue

            if self.exclude_shorts and "/shorts/" in entry.link:
                continue

            video_id = _extract_video_id(entry)
            if video_id is None:
                logger.warning("Skipping entry without video id: %s", entry.link)
                continue

            videos.append(
                VideoData(
                    video_id=video_id,
                    title=entry.title,
                    description=entry.get("summary", ""),
                    published_at=published,
                    url=entry.link,
                    channel_title=entry.get("author", ""),
                    thumbnail_url=youtube_thumbnail_url(video_id),
                )
            )

        videos.sort(key=lambda video: video.published_at, reverse=True)
        return videos

    def get_transcript(self, video_id: str) -> Transcript:
        fetched = self.ytt_api.fetch(video_id, languages=self.transcript_languages)
        snippets = [
            TranscriptSnippet(
                text=snippet.text,
                start=snippet.start,
                duration=snippet.duration,
            )
            for snippet in fetched.snippets
        ]
        text = " ".join(snippet.text for snippet in snippets)
        return Transcript(
            text=text,
            language=fetched.language,
            language_code=fetched.language_code,
            is_generated=fetched.is_generated,
            snippets=snippets,
        )

    def get_channel_videos_with_transcripts(
        self, channel_id: str, hours: int = 168
    ) -> list[VideoData]:
        videos = self.get_channel_videos(channel_id, hours)

        for video in videos:
            try:
                video.transcript = self.get_transcript(video.video_id)
            except YouTubeTranscriptApiException as error:
                video.transcript_error = str(error)
                logger.warning(
                    "Transcript unavailable for %s: %s",
                    video.video_id,
                    error,
                )

        return videos
