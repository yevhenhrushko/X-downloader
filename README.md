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

## Usage

```bash
./download <url>
```

## Examples

```bash
# X/Twitter - image
./download "https://x.com/FermusP/status/2040698457007001753/photo/1"

# X/Twitter - video
./download "https://x.com/i/status/2040652343121731860"

# Instagram - post
./download "https://www.instagram.com/p/ABC123/"

# Instagram - reel
./download "https://www.instagram.com/reel/XYZ789/"

# Instagram - story
./download "https://www.instagram.com/stories/username/1234567890"

# Telegram - single message
./download "https://t.me/channel/123"

# Telegram - full channel (downloads ALL media, 10 parallel threads)
./download "https://t.me/channel"
./download "https://web.telegram.org/a/#-1002899724101"
```

## Output

**Single post**: `downloads/@username_ID.ext`

**Multiple media in one post**: `downloads/@username_ID_1.ext`, `@username_ID_2.ext`

**Full Telegram channel**: `downloads/ChannelName/ID.ext` (subfolder per channel)

## Supported Platforms

| Platform | Images | Video | Full Channel | Auth |
|----------|--------|-------|-------------|------|
| X/Twitter | yes | yes | no | Optional (NSFW/private) |
| Instagram | yes | yes | no | Recommended |
| Telegram | yes | yes | yes (10 threads) | Required (Telegram API) |

## Notes

- Shortlink URLs (`x.com/i/status/...`) resolve to real username
- Videos download in best quality (merged with ffmpeg)
- VP9 video auto-converted to H.264 for universal playback
- Images download in original resolution
- Full channel download skips already downloaded files
- web.telegram.org URLs are supported
- If cookies expire, re-export from browser and replace the file

## Dependencies

- Python 3.13+
- ffmpeg (via Homebrew: `brew install ffmpeg`)
- yt-dlp (video downloads)
- gallery-dl (image downloads)
- telethon (Telegram API)
