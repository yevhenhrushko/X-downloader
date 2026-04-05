# X-Downloader

CLI tool to download videos and images from X (Twitter), Instagram, and Telegram in best quality.

## Setup (one-time)

```bash
cd X-downloader
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### Cookies

Export cookies from your browser using a cookie extension (e.g., "Get cookies.txt") and save to the project root:

- `x_cookies.txt` — X/Twitter (rename from `x.com_cookies.txt`)
- `www.instagram.com_cookies.txt` — Instagram

### Telegram Setup

Telegram uses the Telegram API (not cookies). One-time setup:

```bash
./venv/bin/python setup_telegram.py
```

Enter your phone number and the code Telegram sends you. This creates a `telegram.session` file for future use.

### Check Cookie Health

```bash
./download --check
```

Reports status and expiry for all cookie files and Telegram session.

## Usage

```bash
./download <url>                          # Single URL
./download <url1> <url2> <url3>           # Multiple URLs (batch)
./download -c                             # Download from clipboard
./download -f urls.txt                    # Download from file (one URL per line)
./download --force <url>                  # Re-download even if exists
```

## Examples

```bash
# X/Twitter
./download "https://x.com/user/status/1234567890"

# Instagram - post/reel/story
./download "https://www.instagram.com/p/ABC123/"
./download "https://www.instagram.com/reel/XYZ789/"
./download "https://www.instagram.com/stories/username/1234567890"

# Telegram - single message
./download "https://t.me/channel/123"

# Telegram - full channel (10 parallel downloads)
./download "https://t.me/channel"
./download "https://web.telegram.org/a/#-1002899724101"

# Batch - multiple URLs at once
./download "https://x.com/a/status/1" "https://instagram.com/p/ABC" "https://t.me/ch/5"

# Clipboard - copy URL in browser, then
./download -c

# From file
./download -f saved_urls.txt
```

## Output

Files are organized by platform:

```
downloads/
  twitter/        @username_ID.ext
  instagram/      @username_ID.ext
  telegram/
    ChannelName/  ID.ext
```

## Features

| Feature | Description |
|---------|-------------|
| Multi-platform | X/Twitter, Instagram, Telegram |
| Batch download | Multiple URLs, file input, clipboard |
| Duplicate skip | Auto-skips already downloaded files |
| Full channel | Download entire Telegram channels (10 threads) |
| Best quality | Highest resolution, VP9 auto-converted to H.264 |
| Cookie check | `--check` validates all auth |
| Platform folders | Organized by platform automatically |

## Supported Platforms

| Platform | Images | Video | Full Channel | Auth |
|----------|--------|-------|-------------|------|
| X/Twitter | yes | yes | no | Optional (NSFW/private) |
| Instagram | yes | yes | no | Recommended |
| Telegram | yes | yes | yes (10 threads) | Required (Telegram API) |

## Dependencies

- Python 3.13+
- ffmpeg (via Homebrew: `brew install ffmpeg`)
- yt-dlp, gallery-dl, telethon, requests (via pip)
