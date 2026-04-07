# Telegram Downloader Bot Design Spec

**Date**: 2026-04-05
**Status**: Approved

## Purpose

CLI script to download videos and images from X (Twitter) in best quality. Takes a tweet URL as input, saves media to a local folder with consistent naming.

## Usage

```bash
python download.py https://x.com/username/status/1234567890
```

Output:
```
downloads/@username_1234567890.mp4
downloads/@username_1234567890_1.jpg   # multiple media
downloads/@username_1234567890_2.jpg
```

## Architecture

**Single file**: `download.py` — thin CLI wrapper around yt-dlp's Python API.

### Flow

1. Parse URL, extract tweet ID
2. Call yt-dlp Python API with cookie file and best quality settings
3. yt-dlp downloads media to a temp location
4. Script renames files to `@username_ID[_N].ext` format
5. Move to `downloads/` directory
6. Print result path(s) to stdout

## Authentication

Cookie-based auth using `cookies.txt` in Netscape format at the project root (`telegram-downloader-bot/cookies.txt`). Exported from browser using a cookie export extension.

yt-dlp reads this natively via `--cookies` / `cookiefile` option.

If `cookies.txt` is missing: print a warning and attempt without auth. Will fail on restricted content (NSFW, private, age-gated).

## Quality Selection

- **Video**: `bestvideo+bestaudio/best` — highest quality video + audio merged with ffmpeg
- **Images**: yt-dlp extracts highest resolution variant (`?format=jpg&name=orig`)

## File Naming

Format: `@{username}_{tweet_id}[_{index}].{ext}`

- Single media: `@username_1234567890.mp4`
- Multiple media: `@username_1234567890_1.jpg`, `@username_1234567890_2.jpg`, etc.

Index suffix only added when tweet contains more than one media item.

## Multi-Media Tweets

yt-dlp downloads all media items from a tweet. The script numbers them sequentially with `_1`, `_2`, etc.

## Output Directory

`telegram-downloader-bot/downloads/` — created automatically if it doesn't exist.

## Error Handling

- **Invalid URL**: Validate against `https://(x.com|twitter.com)/*/status/*` pattern. Clear error message, non-zero exit code
- **Missing cookies.txt**: Warning printed, attempt without auth
- **Network/download errors**: yt-dlp's built-in retry logic (3 retries by default)
- **ffmpeg missing**: yt-dlp falls back to single-stream download with warning

## Dependencies

- `yt-dlp` — pip install
- `ffmpeg` — already installed on system (via Homebrew)
- Python 3.13 — already installed

## Files

```
telegram-downloader-bot/
  download.py          # main script
  cookies.txt          # browser cookies (user-provided, gitignored)
  downloads/           # output directory (gitignored)
  requirements.txt     # yt-dlp
  .gitignore
```

## Out of Scope

- GUI or web interface
- Batch mode / URL list processing
- Twitter API integration
- Scheduling or monitoring
- Metadata storage (JSON sidecar files, etc.)
