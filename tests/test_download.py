import pytest
from download import (
    build_filenames,
    detect_platform,
    parse_instagram_url,
    parse_telegram_url,
    parse_tweet_url,
)


class TestDetectPlatform:
    def test_x_com(self):
        assert detect_platform("https://x.com/user/status/123") == "twitter"

    def test_twitter_com(self):
        assert detect_platform("https://twitter.com/user/status/123") == "twitter"

    def test_mobile_twitter(self):
        assert detect_platform("https://mobile.twitter.com/user/status/123") == "twitter"

    def test_instagram(self):
        assert detect_platform("https://www.instagram.com/p/ABC123/") == "instagram"

    def test_instagram_no_www(self):
        assert detect_platform("https://instagram.com/reel/ABC123/") == "instagram"

    def test_telegram(self):
        assert detect_platform("https://t.me/channel/123") == "telegram"

    def test_web_telegram(self):
        assert detect_platform("https://web.telegram.org/a/#-1002899724101") == "telegram"

    def test_unsupported(self):
        with pytest.raises(ValueError, match="Unsupported platform"):
            detect_platform("https://youtube.com/watch?v=123")

    def test_empty(self):
        with pytest.raises(ValueError):
            detect_platform("")


class TestParseTweetUrl:
    def test_standard_x_url(self):
        assert parse_tweet_url("https://x.com/elonmusk/status/1234567890") == ("elonmusk", "1234567890")

    def test_twitter_url(self):
        assert parse_tweet_url("https://twitter.com/jack/status/9876543210") == ("jack", "9876543210")

    def test_url_with_query_params(self):
        assert parse_tweet_url("https://x.com/user/status/111?s=20&t=abc") == ("user", "111")

    def test_url_with_trailing_slash(self):
        assert parse_tweet_url("https://x.com/user/status/111/") == ("user", "111")

    def test_mobile_url(self):
        assert parse_tweet_url("https://mobile.twitter.com/user/status/111") == ("user", "111")

    def test_invalid_url_not_twitter(self):
        with pytest.raises(ValueError, match="Not a valid X/Twitter URL"):
            parse_tweet_url("https://youtube.com/watch?v=123")

    def test_invalid_url_no_status(self):
        with pytest.raises(ValueError, match="Not a valid X/Twitter URL"):
            parse_tweet_url("https://x.com/elonmusk")

    def test_invalid_url_empty(self):
        with pytest.raises(ValueError, match="Not a valid X/Twitter URL"):
            parse_tweet_url("")


class TestParseInstagramUrl:
    def test_post(self):
        assert parse_instagram_url("https://www.instagram.com/p/ABC123/") == (None, "ABC123")

    def test_reel(self):
        assert parse_instagram_url("https://www.instagram.com/reel/XYZ789/") == (None, "XYZ789")

    def test_reels(self):
        assert parse_instagram_url("https://instagram.com/reels/DEF456/") == (None, "DEF456")

    def test_story(self):
        assert parse_instagram_url("https://www.instagram.com/stories/natgeo/1234567890") == ("natgeo", "1234567890")

    def test_post_no_trailing_slash(self):
        assert parse_instagram_url("https://instagram.com/p/ABC123") == (None, "ABC123")

    def test_invalid(self):
        with pytest.raises(ValueError, match="Not a valid Instagram URL"):
            parse_instagram_url("https://instagram.com/user")

    def test_empty(self):
        with pytest.raises(ValueError, match="Not a valid Instagram URL"):
            parse_instagram_url("")


class TestParseTelegramUrl:
    # Single message URLs
    def test_public_channel_message(self):
        assert parse_telegram_url("https://t.me/durov/123") == ("durov", "123")

    def test_private_channel_message(self):
        assert parse_telegram_url("https://t.me/c/1234567890/456") == ("c/1234567890", "456")

    def test_trailing_slash(self):
        assert parse_telegram_url("https://t.me/channel/789/") == ("channel", "789")

    # Full channel URLs (message_id=None)
    def test_public_channel_only(self):
        assert parse_telegram_url("https://t.me/durov") == ("durov", None)

    def test_private_channel_only(self):
        assert parse_telegram_url("https://t.me/c/1234567890") == ("c/1234567890", None)

    # web.telegram.org URLs
    def test_web_telegram_channel(self):
        assert parse_telegram_url("https://web.telegram.org/a/#-1002899724101") == ("c/2899724101", None)

    def test_web_telegram_message(self):
        assert parse_telegram_url("https://web.telegram.org/a/#-1002899724101/739") == ("c/2899724101", "739")

    def test_invalid_empty(self):
        with pytest.raises(ValueError, match="Not a valid Telegram URL"):
            parse_telegram_url("")


class TestBuildFilenames:
    def test_single_video(self):
        assert build_filenames("elonmusk", "123", ["video.mp4"]) == {"video.mp4": "@elonmusk_123.mp4"}

    def test_single_image(self):
        assert build_filenames("user", "456", ["photo.jpg"]) == {"photo.jpg": "@user_456.jpg"}

    def test_multiple_media(self):
        assert build_filenames("user", "789", ["a.jpg", "b.png", "c.mp4"]) == {
            "a.jpg": "@user_789_1.jpg",
            "b.png": "@user_789_2.png",
            "c.mp4": "@user_789_3.mp4",
        }

    def test_preserves_extension(self):
        assert build_filenames("user", "1", ["file.webm"]) == {"file.webm": "@user_1.webm"}
