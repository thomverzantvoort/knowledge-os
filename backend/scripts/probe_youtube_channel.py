import logging

from youtube_transcript_api import YouTubeTranscriptApiException

from app.ingest.adapters.youtube import Transcript, VideoData, YouTubeScraper


def _print_transcript(transcript: Transcript) -> None:
    print("Transcript")
    print("  language:", transcript.language_code)
    print("  auto_generated:", transcript.is_generated)
    print("  snippet_count:", len(transcript.snippets))
    print("  char_count:", len(transcript.text))
    print("  preview:", transcript.text[:300])


def _print_video_summary(video: VideoData) -> None:
    print()
    print(video.video_id, "|", video.title)
    print("  published:", video.published_at.isoformat())
    print("  url:", video.url)
    print("  thumbnail:", video.thumbnail_url)
    print("  channel:", video.channel_title)
    print("  description_chars:", len(video.description))
    if video.transcript:
        print("  transcript_language:", video.transcript.language_code)
        print("  transcript_auto_generated:", video.transcript.is_generated)
        print("  transcript_chars:", len(video.transcript.text))
    elif video.transcript_error:
        print("  transcript_error:", video.transcript_error)
    else:
        print("  transcript: not fetched")


def _print_channel_summary(videos: list[VideoData]) -> None:
    with_transcript = sum(1 for video in videos if video.transcript)
    without_transcript = sum(1 for video in videos if video.transcript_error)
    print()
    print("Channel summary")
    print("  videos_in_window:", len(videos))
    print("  with_transcript:", with_transcript)
    print("  transcript_errors:", without_transcript)
    for video in videos:
        _print_video_summary(video)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # change these when testing
    CHANNEL_ID = "UCMyQ9rJgl1oI0c-HfoYRIAQ"
    HOURS = 336
    SINGLE_VIDEO_ID = "XCWcB1aXY84"
    TRANSCRIPT_LANGUAGES = ["en", "nl"]
    EXCLUDE_SHORTS = True

    scraper = YouTubeScraper(
        transcript_languages=TRANSCRIPT_LANGUAGES,
        exclude_shorts=EXCLUDE_SHORTS,
    )

    # optional: one video transcript only
    print("Single video probe:", SINGLE_VIDEO_ID)
    try:
        transcript = scraper.get_transcript(SINGLE_VIDEO_ID)
        _print_transcript(transcript)
    except YouTubeTranscriptApiException as error:
        print("  transcript_error:", error)

    print()
    print("Channel probe:", CHANNEL_ID, "hours:", HOURS)
    videos = scraper.get_channel_videos_with_transcripts(CHANNEL_ID, hours=HOURS)
    _print_channel_summary(videos)
