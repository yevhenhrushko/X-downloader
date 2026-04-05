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
- `web.telegram.org_cookies.txt` — Telegram

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

# Telegram
./download "https://t.me/channel/123"
```

## Output

Files saved to `downloads/` folder with format:
- Single media: `@username_ID.ext`
- Multiple media: `@username_ID_1.ext`, `@username_ID_2.ext`

## Supported Platforms

| Platform | Images | Video | Auth Required |
|----------|--------|-------|---------------|
| X/Twitter | yes | yes | Optional (needed for NSFW/private) |
| Instagram | yes | yes | Recommended |
| Telegram | yes | yes | Required |

## Notes

- Shortlink URLs (`x.com/i/status/...`) resolve to real username
- Videos download in best quality (merged with ffmpeg)
- Images download in original resolution
- If cookies expire, re-export from browser and replace the file

## Dependencies

- Python 3.13+
- ffmpeg (via Homebrew: `brew install ffmpeg`)
- yt-dlp (video downloads)
- gallery-dl (image downloads)
