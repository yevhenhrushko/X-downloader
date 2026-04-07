# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests (52 tests)
./venv/bin/python -m pytest tests/ -v

# Run specific test class
./venv/bin/python -m pytest tests/test_download.py::TestParseYoutubeUrl -v

# Run the CLI tool
./download "<url>"
./download -c                  # from clipboard
./download url1 url2 url3      # batch
./download -f urls.txt         # from file
./download --mp3 "<url>"       # audio-only (YouTube)
./download --check             # cookie health check

# Install dependencies
./venv/bin/pip install -r requirements.txt

# Telegram one-time setup (creates telegram.session)
./venv/bin/python setup_telegram.py

# Deploy (auto via GitHub Actions on push to master)
# Manual: docker compose up -d --build
```

All Python commands must use `./venv/bin/python` — the project uses a local venv, not system Python.

## Architecture

Two entry points: CLI (`download.py` + `download` wrapper) and Telegram bot (`bot.py`). Both share the same download engine.

```
download.py (CLI)                    bot.py (Telegram bot)
     │                                    │
     ├─ detect_platform()                 ├─ _is_allowed() → ID check
     ├─ parse_{platform}_url()            ├─ _process_url() → download_media()
     ├─ _check_disk_space()               ├─ _handle_youtube_url() → metadata + keyboard
     ├─ _check_duplicate()                ├─ handle_youtube_callback() → Video/MP3
     ├─ _download_{platform}()            ├─ _run_download() → progress + send
     ├─ _ensure_h264()                    ├─ _send_files() → albums of 10
     ├─ build_filenames()                 ├─ _serve_large_file() → nginx link
     └─ _print_summary()                 └─ _handle_channel_download()
```

**Platform dispatch**: `detect_platform(url)` returns `"twitter"`, `"instagram"`, `"telegram"`, or `"youtube"`. Each platform has its own URL parser and download function.

**Download backends**:
- YouTube: yt-dlp for video and audio (supports Shorts, playlists, mp3 extraction)
- Twitter: yt-dlp for video, gallery-dl for images (yt-dlp can't extract image-only tweets)
- Instagram: gallery-dl for everything
- Telegram: telethon (single message = sync API, full channel = async with 10-concurrent semaphore)

**Error handling**: Download functions raise `DownloadError` instead of `sys.exit()`. Bot catches `DownloadError` specifically — unexpected exceptions get sanitized before showing to users. All `status_msg.edit_text` calls go through `_safe_edit()` wrapper.

**Disk space check**: `_check_disk_space()` verifies >=500MB free before any download.

**Telegram channel download**: `_download_telegram_channel` uses `asyncio.run()` internally. When called from bot (already in async context), it must run via `loop.run_in_executor()` to avoid event loop conflict.

**Video post-processing**: `_ensure_h264()` checks codec via ffprobe and re-encodes VP9 to H.264 using ffmpeg. Original file deleted only after successful encode. Skipped for mp3 downloads.

## Bot Architecture (bot.py)

**Access control**: Restricted by Telegram user ID. `ALLOWED_IDS` set checked on every request.

**YouTube flow**: URL detected → metadata fetched (title, channel, duration) → inline keyboard (Video/MP3) → user chooses → download with progress.

**Media sending**: Files sent as documents (no compression). Multiple files grouped into albums (max 10). Files >50MB moved to nginx directory and sent as download links.

**Large file fallback**: `_serve_large_file()` moves file to `NGINX_DIR`, returns URL. Nginx serves on port 9090.

**Cleanup**: `cleanup.sh` cron deletes files older than 24h from both downloads/ and nginx dir.

## Key Conventions

- **Output structure**: `downloads/{platform}/@{username}_{id}[_{index}].{ext}`
- **Telegram channel output**: `downloads/telegram/ChannelName/{msg_id}.{ext}`
- **YouTube output**: `downloads/youtube/@{channel}_{video_id}.{ext}`
- **Duplicate detection**: `_check_duplicate()` globs for existing files. Use `--force` to override.
- **Cookie files**: `x_cookies.txt`, `www.instagram.com_cookies.txt`, `youtube_cookies.txt` — Netscape format, gitignored via `*cookies*.txt`
- **Telegram auth**: telethon session file (`telegram.session`). API credentials via env vars with defaults.
- **URL parsing**: Returns `tuple[str, str]` for (username, id). Telegram returns `tuple[str, str | None]` where None = full channel. YouTube returns `tuple[str, str | None]` for (video_id, playlist_id).
- **Batch mode**: Multiple URLs via args, `--file`, or `--clipboard`. Only `DownloadError` caught in batch loop.
- **Output convention**: File paths to stdout (for piping), everything else to stderr.
- **Bot env vars**: `DOWNLOADER_BOT_TOKEN` (required), `SERVER_HOST`, `NGINX_DIR`, `SERVER_URL`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`

## Deployment

- **Server**: Oracle Cloud (158.180.23.247), user `ubuntu`
- **Path**: `/home/ubuntu/xdownloader/`
- **CI/CD**: Push to `master` → GitHub Actions → SSH deploy → `docker compose up -d --build`
- **Services**: `xdownloader-bot` (Python) + `xdownloader-nginx` (port 9090, large file serving)
- **Secrets**: `DOWNLOADER_BOT_TOKEN`, `OCI_HOST`, `OCI_USER`, `OCI_SSH_KEY`
- **Files on server** (not in git): `x_cookies.txt`, `www.instagram.com_cookies.txt`, `youtube_cookies.txt`, `telegram.session`
