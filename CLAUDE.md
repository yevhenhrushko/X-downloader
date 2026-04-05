# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests (36 tests)
./venv/bin/python -m pytest tests/ -v

# Run specific test class
./venv/bin/python -m pytest tests/test_download.py::TestParseTelegramUrl -v

# Run the tool
./download "<url>"
./download -c                  # from clipboard
./download url1 url2 url3      # batch
./download -f urls.txt         # from file
./download --check             # cookie health check

# Install dependencies
./venv/bin/pip install -r requirements.txt

# Telegram one-time setup (creates telegram.session)
./venv/bin/python setup_telegram.py
```

All Python commands must use `./venv/bin/python` — the project uses a local venv, not system Python.

## Architecture

Single-file CLI (`download.py`) with a shell wrapper (`download`). Uses argparse for CLI flags.

```
URL → detect_platform() → parse_{platform}_url() → duplicate check
    → _download_{platform}(url, tmpdir) → _collect_files() → _ensure_h264()
    → build_filenames() → move to downloads/{platform}/ → _print_summary()
```

**Platform dispatch**: `detect_platform(url)` returns `"twitter"`, `"instagram"`, or `"telegram"`. Each platform has its own URL parser and download function.

**Download backends**:
- Twitter: yt-dlp for video, gallery-dl for images (yt-dlp can't extract image-only tweets)
- Instagram: gallery-dl for everything
- Telegram: telethon (single message = sync API, full channel = async with 10-concurrent semaphore)

**Error handling**: Download functions raise `DownloadError` instead of `sys.exit()`. This allows batch mode to continue on failures. Only `main()` calls `sys.exit()`.

**Telegram has two modes**: single message (returns to normal rename flow) and full channel download (`_download_telegram_channel`) which bypasses the tmpdir pattern — downloads directly to `downloads/telegram/ChannelName/` with async parallelism.

**Video post-processing**: `_ensure_h264()` checks codec via ffprobe and re-encodes VP9 to H.264 using ffmpeg. Applied to all platforms.

## Key Conventions

- **Output structure**: `downloads/{platform}/@{username}_{id}[_{index}].{ext}` — organized by platform subfolder
- **Telegram channel output**: `downloads/telegram/ChannelName/{msg_id}.{ext}`
- **Duplicate detection**: `_check_duplicate()` globs for existing files before downloading. Skipped files still appear in output. Use `--force` to override.
- **Cookie files**: `x_cookies.txt`, `www.instagram.com_cookies.txt`, `web.telegram.org_cookies.txt` — Netscape format, gitignored via `*cookies*.txt`
- **Telegram auth**: Uses telethon session file (`telegram.session`), not cookies. API credentials in download.py (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`)
- **URL parsing**: Returns `tuple[str, str]` for (username, id). Telegram's `parse_telegram_url` returns `tuple[str, str | None]` where None message_id means full channel download
- **Batch mode**: Multiple URLs via args, `--file`, or `--clipboard`. Failures don't stop the batch. Summary printed at end.
- **Output convention**: File paths go to stdout (for piping), everything else to stderr
