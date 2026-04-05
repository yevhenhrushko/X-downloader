#!/usr/bin/env python3
"""Download videos and images from X/Twitter, Instagram, and Telegram in best quality."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests
import yt_dlp

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
COOKIES_FILES = {
    "twitter": SCRIPT_DIR / "x_cookies.txt",
    "instagram": SCRIPT_DIR / "www.instagram.com_cookies.txt",
    "telegram": SCRIPT_DIR / "web.telegram.org_cookies.txt",
}
VENV_BIN = SCRIPT_DIR / "venv" / "bin"


def detect_platform(url: str) -> str:
    """Detect platform from URL. Returns 'twitter', 'instagram', or 'telegram'.

    Raises ValueError if URL doesn't match any supported platform.
    """
    parsed = urlparse(url.strip())
    domain = parsed.netloc.lower().removeprefix("www.").removeprefix("mobile.")
    if domain in ("x.com", "twitter.com"):
        return "twitter"
    if domain == "instagram.com":
        return "instagram"
    if domain in ("t.me", "web.telegram.org"):
        return "telegram"
    raise ValueError(f"Unsupported platform: {domain}")


def parse_tweet_url(url: str) -> tuple[str, str]:
    """Extract (username, tweet_id) from an X/Twitter URL.

    Raises ValueError if URL doesn't match expected pattern.
    """
    pattern = r"https?://(?:mobile\.)?(?:x\.com|twitter\.com)/([^/]+)/status/(\d+)"
    match = re.match(pattern, url.strip().rstrip("/"))
    if not match:
        raise ValueError(f"Not a valid X/Twitter URL: {url}")
    return match.group(1), match.group(2)


def parse_instagram_url(url: str) -> tuple[str | None, str]:
    """Extract (username_or_none, shortcode) from an Instagram URL.

    Supports: /p/CODE, /reel/CODE, /stories/USER/ID, /reels/CODE
    Raises ValueError if URL doesn't match expected pattern.
    """
    url = url.strip().rstrip("/")
    # Posts and reels: /p/CODE or /reel/CODE or /reels/CODE
    match = re.match(r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels)/([A-Za-z0-9_-]+)", url)
    if match:
        return None, match.group(1)
    # Stories: /stories/USER/ID
    match = re.match(r"https?://(?:www\.)?instagram\.com/stories/([^/]+)/(\d+)", url)
    if match:
        return match.group(1), match.group(2)
    raise ValueError(f"Not a valid Instagram URL: {url}")


def parse_telegram_url(url: str) -> tuple[str, str | None]:
    """Extract (channel, message_id_or_none) from a Telegram URL.

    Supports:
      t.me/channel/123, t.me/c/1234567890/123 (single message)
      t.me/channel, t.me/c/1234567890 (full channel)
      web.telegram.org/a/#-100CHANNELID (full channel)
      web.telegram.org/a/#-100CHANNELID/MSGID (single message)
    Returns message_id=None for full channel download.
    Raises ValueError if URL doesn't match expected pattern.
    """
    url = url.strip().rstrip("/")

    # web.telegram.org/a/#-100CHANNELID or web.telegram.org/a/#-100CHANNELID/MSGID
    match = re.match(r"https?://web\.telegram\.org/a/#(-?\d+)(?:/(\d+))?", url)
    if match:
        raw_id = match.group(1)
        # Web IDs are like -1002899724101 -> strip -100 prefix to get channel ID
        channel_id = raw_id.lstrip("-")
        if channel_id.startswith("100"):
            channel_id = channel_id[3:]
        return f"c/{channel_id}", match.group(2)  # msg_id is None if not present

    # t.me/c/channel_id/message_id
    match = re.match(r"https?://t\.me/c/(\d+)/(\d+)", url)
    if match:
        return f"c/{match.group(1)}", match.group(2)

    # t.me/c/channel_id (full channel, no message)
    match = re.match(r"https?://t\.me/c/(\d+)$", url)
    if match:
        return f"c/{match.group(1)}", None

    # t.me/channel/message_id
    match = re.match(r"https?://t\.me/([^/]+)/(\d+)", url)
    if match:
        return match.group(1), match.group(2)

    # t.me/channel (full channel, no message)
    match = re.match(r"https?://t\.me/([^/]+)$", url)
    if match:
        return match.group(1), None

    raise ValueError(f"Not a valid Telegram URL: {url}")


def build_filenames(username: str, media_id: str, original_files: list[str]) -> dict[str, str]:
    """Map original filenames to @username_mediaID[_N].ext format.

    Returns dict of {original_name: new_name}.
    No index suffix for single files; _1, _2, etc. for multiple.
    """
    result = {}
    use_index = len(original_files) > 1
    for i, orig in enumerate(original_files, start=1):
        ext = Path(orig).suffix
        if use_index:
            new_name = f"@{username}_{media_id}_{i}{ext}"
        else:
            new_name = f"@{username}_{media_id}{ext}"
        result[orig] = new_name
    return result


def _get_cookies(platform: str) -> Path | None:
    """Get cookies file path for platform, or None if missing."""
    path = COOKIES_FILES.get(platform)
    if path and path.exists():
        return path
    return None


# --- Twitter ---

def _extract_tweet_info(url: str) -> dict:
    """Extract tweet metadata using yt-dlp."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignore_no_formats_error": True,
    }
    cookies = _get_cookies("twitter")
    if cookies:
        ydl_opts["cookiefile"] = str(cookies)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info or {}


def _download_twitter_video(url: str, tmpdir: str) -> None:
    """Download video using yt-dlp (best quality with ffmpeg merge)."""
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": os.path.join(tmpdir, "%(id)s_%(autonumber)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": False,
    }
    cookies = _get_cookies("twitter")
    if cookies:
        ydl_opts["cookiefile"] = str(cookies)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def _download_twitter_images(url: str, tmpdir: str) -> None:
    """Download images using gallery-dl."""
    cmd = [
        str(VENV_BIN / "gallery-dl"),
        "-d", tmpdir,
        "--filename", "{tweet_id}_{num}.{extension}",
        "--no-mtime",
    ]
    cookies = _get_cookies("twitter")
    if cookies:
        cmd.extend(["--cookies", str(cookies)])
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"gallery-dl error: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def _download_twitter(url: str, tmpdir: str) -> tuple[str, str]:
    """Download Twitter media. Returns (username, tweet_id)."""
    url_username, tweet_id = parse_tweet_url(url)
    info = _extract_tweet_info(url)
    username = info.get("uploader_id") or url_username
    if bool(info.get("formats")):
        _download_twitter_video(url, tmpdir)
    else:
        _download_twitter_images(url, tmpdir)
    return username, tweet_id


# --- Instagram ---

def _download_instagram(url: str, tmpdir: str) -> tuple[str, str]:
    """Download Instagram media via gallery-dl. Returns (username, post_id)."""
    url_username, shortcode = parse_instagram_url(url)
    cmd = [
        str(VENV_BIN / "gallery-dl"),
        "-d", tmpdir,
        "--filename", "{filename}.{extension}",
        "--no-mtime",
    ]
    cookies = _get_cookies("instagram")
    if cookies:
        cmd.extend(["--cookies", str(cookies)])
    else:
        print("Warning: instagram_cookies.txt not found. Some content may not be accessible.", file=sys.stderr)
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"gallery-dl error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Try to extract username from gallery-dl output path (twitter/USERNAME/...)
    username = url_username or "unknown"
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            parts = Path(line.strip()).parts
            # gallery-dl creates: tmpdir/instagram/USERNAME/file
            for j, part in enumerate(parts):
                if part == "instagram" and j + 1 < len(parts):
                    username = parts[j + 1]
                    break

    return username, shortcode


# --- Telegram ---

TELEGRAM_API_ID = 34456187
TELEGRAM_API_HASH = "f451a6ed6c0b0f596bdbb7a5f3938440"
TELEGRAM_SESSION = str(SCRIPT_DIR / "telegram")


def _resolve_telegram_entity(client, channel: str):
    """Resolve a telegram channel string to an entity."""
    if channel.startswith("c/"):
        channel_id = int(f"-100{channel.split('/')[1]}")
        return client.get_entity(channel_id)
    return client.get_entity(channel)


def _get_telegram_channel_name(entity, fallback: str) -> str:
    """Get a clean channel name for file naming."""
    name = getattr(entity, 'username', None) or getattr(entity, 'title', fallback)
    return name.replace("/", "_").replace(" ", "_")


def _download_telegram(url: str, tmpdir: str) -> tuple[str, str]:
    """Download single Telegram message media. Returns (channel_name, message_id)."""
    from telethon.sync import TelegramClient

    channel, message_id = parse_telegram_url(url)

    session_path = Path(TELEGRAM_SESSION + ".session")
    if not session_path.exists():
        print("Error: Telegram session not found. Run: ./venv/bin/python setup_telegram.py", file=sys.stderr)
        sys.exit(1)

    with TelegramClient(TELEGRAM_SESSION, TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
        entity = _resolve_telegram_entity(client, channel)
        channel_name = _get_telegram_channel_name(entity, channel)

        msg = client.get_messages(entity, ids=int(message_id))
        if not msg or not msg.media:
            print("Error: No media found in this Telegram message.", file=sys.stderr)
            sys.exit(1)

        path = client.download_media(msg, file=tmpdir)
        if path:
            print(f"Downloaded: {os.path.basename(path)}", file=sys.stderr)

    return channel_name, message_id


def _download_telegram_channel(url: str) -> list[str]:
    """Download all media from a Telegram channel with async parallel. Returns saved file paths."""
    import asyncio
    from telethon import TelegramClient as AsyncTelegramClient

    channel, _ = parse_telegram_url(url)

    session_path = Path(TELEGRAM_SESSION + ".session")
    if not session_path.exists():
        print("Error: Telegram session not found. Run: ./venv/bin/python setup_telegram.py", file=sys.stderr)
        sys.exit(1)

    async def _run():
        client = AsyncTelegramClient(TELEGRAM_SESSION, TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.start()

        entity = await client.get_entity(
            int(f"-100{channel.split('/')[1]}") if channel.startswith("c/") else channel
        )
        channel_name = getattr(entity, 'username', None) or getattr(entity, 'title', channel)
        channel_name = channel_name.replace("/", "_").replace(" ", "_")

        # Create subfolder per channel
        channel_dir = DOWNLOADS_DIR / channel_name
        channel_dir.mkdir(parents=True, exist_ok=True)

        # Collect all messages with media
        print(f"Scanning channel: {channel_name}...", file=sys.stderr)
        media_messages = []
        async for msg in client.iter_messages(entity):
            if msg.photo or msg.video or msg.document:
                media_messages.append(msg)
        total = len(media_messages)
        print(f"Found {total} media messages.", file=sys.stderr)

        if total == 0:
            await client.disconnect()
            return []

        saved_paths = []
        counter = 0
        sem = asyncio.Semaphore(10)  # 10 parallel downloads

        async def download_one(msg):
            nonlocal counter
            async with sem:
                # Check if already downloaded
                existing = list(channel_dir.glob(f"{msg.id}.*"))
                if existing:
                    counter += 1
                    return str(existing[0])

                path = await client.download_media(msg, file=str(channel_dir))
                if path:
                    actual_ext = Path(path).suffix
                    final_name = f"{msg.id}{actual_ext}"
                    final_path = channel_dir / final_name
                    if Path(path) != final_path:
                        Path(path).rename(final_path)
                    counter += 1
                    print(f"\r  [{counter}/{total}] {final_name}", file=sys.stderr, end="", flush=True)
                    return str(final_path)
                counter += 1
                return None

        # Launch all downloads with semaphore limiting concurrency
        tasks = [download_one(msg) for msg in media_messages]
        results = await asyncio.gather(*tasks)
        saved_paths = [r for r in results if r]

        print(f"\n  Done: {len(saved_paths)}/{total} files downloaded.", file=sys.stderr)
        await client.disconnect()
        return saved_paths

    return asyncio.run(_run())


def _load_cookies_as_dict(cookies_path: Path) -> dict:
    """Load Netscape cookies file into a dict for requests."""
    cookies = {}
    with open(cookies_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                cookies[parts[5]] = parts[6]
    return cookies


# --- Common ---

def _ensure_h264(filepath: str) -> str:
    """Re-encode video to H.264 if it uses VP9 or other incompatible codecs. Returns final path."""
    if not filepath.lower().endswith((".mp4", ".webm", ".mkv")):
        return filepath
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name", "-of", "csv=p=0", filepath],
        capture_output=True, text=True,
    )
    codec = probe.stdout.strip()
    if codec and codec != "h264":
        out_path = filepath.rsplit(".", 1)[0] + "_h264.mp4"
        print(f"Re-encoding {codec} -> H.264...", file=sys.stderr)
        subprocess.run(
            ["ffmpeg", "-i", filepath, "-c:v", "libx264", "-preset", "fast",
             "-crf", "18", "-c:a", "aac", "-y", "-loglevel", "warning", out_path],
            check=True,
        )
        os.remove(filepath)
        # Rename back to original name
        final_path = filepath.rsplit(".", 1)[0] + ".mp4"
        os.rename(out_path, final_path)
        return final_path
    return filepath


def _collect_files(tmpdir: str) -> list[str]:
    """Recursively collect all downloaded files from tmpdir."""
    files = []
    for root, _, filenames in os.walk(tmpdir):
        for f in filenames:
            files.append(os.path.join(root, f))
    files.sort()
    return files


def download_media(url: str) -> list[str]:
    """Download all media from a URL. Returns list of saved file paths."""
    platform = detect_platform(url)

    DOWNLOADS_DIR.mkdir(exist_ok=True)

    # Telegram full channel download has its own flow (parallel, direct to downloads/)
    if platform == "telegram":
        _, message_id = parse_telegram_url(url)
        if message_id is None:
            return _download_telegram_channel(url)

    with tempfile.TemporaryDirectory() as tmpdir:
        if platform == "twitter":
            username, media_id = _download_twitter(url, tmpdir)
        elif platform == "instagram":
            username, media_id = _download_instagram(url, tmpdir)
        elif platform == "telegram":
            username, media_id = _download_telegram(url, tmpdir)

        # Collect all downloaded files and ensure video compatibility
        downloaded_paths = _collect_files(tmpdir)
        downloaded_paths = [_ensure_h264(p) for p in downloaded_paths]
        if not downloaded_paths:
            print("Error: No media files were downloaded.", file=sys.stderr)
            sys.exit(1)

        # Extract just filenames for renaming
        downloaded_names = [os.path.basename(p) for p in downloaded_paths]
        name_map = build_filenames(username, media_id, downloaded_names)

        saved_paths = []
        for full_path, orig_name in zip(downloaded_paths, downloaded_names):
            new_name = name_map[orig_name]
            dst = DOWNLOADS_DIR / new_name
            shutil.move(full_path, dst)
            saved_paths.append(str(dst))

    return saved_paths


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <url>", file=sys.stderr)
        print("Supports: X/Twitter, Instagram, Telegram", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    try:
        detect_platform(url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    saved = download_media(url)
    for path in saved:
        print(path)


if __name__ == "__main__":
    main()
