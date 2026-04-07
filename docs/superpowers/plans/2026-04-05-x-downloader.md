# Telegram Downloader Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI script that downloads videos and images from X/Twitter in best quality using yt-dlp.

**Architecture:** Single-file Python CLI (`download.py`) wrapping yt-dlp's Python API. Parses tweet URL, downloads media to a temp directory, renames to `@username_tweetID` format, moves to `downloads/`.

**Tech Stack:** Python 3.13, yt-dlp, ffmpeg

**Project root:** `/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot`

---

## File Structure

```
telegram-downloader-bot/
  download.py          # CLI entry point + all logic
  requirements.txt     # yt-dlp dependency
  .gitignore           # ignore cookies, downloads, __pycache__
  cookies.txt          # user-provided (gitignored)
  downloads/           # output dir (gitignored)
  tests/
    test_download.py   # unit tests for URL parsing, naming logic
```

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```
yt-dlp
```

- [ ] **Step 2: Create .gitignore**

```
cookies.txt
downloads/
__pycache__/
*.pyc
.env
```

- [ ] **Step 3: Install dependencies**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && pip3 install -r requirements.txt`

Expected: yt-dlp installs successfully.

- [ ] **Step 4: Initialize git repo**

```bash
cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot"
git init
git add requirements.txt .gitignore
git commit -m "chore: initialize project with requirements and gitignore"
```

---

### Task 2: URL parsing and validation

**Files:**
- Create: `download.py` (partial — URL parsing functions only)
- Create: `tests/test_download.py` (URL parsing tests)

- [ ] **Step 1: Write failing tests for URL parsing**

Create `tests/test_download.py`:

```python
import pytest
from download import parse_tweet_url


class TestParseTweetUrl:
    def test_standard_x_url(self):
        result = parse_tweet_url("https://x.com/elonmusk/status/1234567890")
        assert result == ("elonmusk", "1234567890")

    def test_twitter_url(self):
        result = parse_tweet_url("https://twitter.com/jack/status/9876543210")
        assert result == ("jack", "9876543210")

    def test_url_with_query_params(self):
        result = parse_tweet_url("https://x.com/user/status/111?s=20&t=abc")
        assert result == ("user", "111")

    def test_url_with_trailing_slash(self):
        result = parse_tweet_url("https://x.com/user/status/111/")
        assert result == ("user", "111")

    def test_mobile_url(self):
        result = parse_tweet_url("https://mobile.twitter.com/user/status/111")
        assert result == ("user", "111")

    def test_invalid_url_not_twitter(self):
        with pytest.raises(ValueError, match="Not a valid X/Twitter URL"):
            parse_tweet_url("https://youtube.com/watch?v=123")

    def test_invalid_url_no_status(self):
        with pytest.raises(ValueError, match="Not a valid X/Twitter URL"):
            parse_tweet_url("https://x.com/elonmusk")

    def test_invalid_url_empty(self):
        with pytest.raises(ValueError, match="Not a valid X/Twitter URL"):
            parse_tweet_url("")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 -m pytest tests/test_download.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'download'` or `ImportError`

- [ ] **Step 3: Implement parse_tweet_url**

Create `download.py`:

```python
#!/usr/bin/env python3
"""Download videos and images from X/Twitter in best quality."""

import re
import sys


def parse_tweet_url(url: str) -> tuple[str, str]:
    """Extract (username, tweet_id) from an X/Twitter URL.

    Raises ValueError if URL doesn't match expected pattern.
    """
    pattern = r"https?://(?:mobile\.)?(?:x\.com|twitter\.com)/([^/]+)/status/(\d+)"
    match = re.match(pattern, url.strip().rstrip("/"))
    if not match:
        raise ValueError(f"Not a valid X/Twitter URL: {url}")
    return match.group(1), match.group(2)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 -m pytest tests/test_download.py -v`

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add download.py tests/test_download.py
git commit -m "feat: add URL parsing with validation"
```

---

### Task 3: File naming logic

**Files:**
- Modify: `download.py` — add `build_filename` function
- Modify: `tests/test_download.py` — add naming tests

- [ ] **Step 1: Write failing tests for file naming**

Append to `tests/test_download.py`:

```python
from download import build_filenames


class TestBuildFilenames:
    def test_single_video(self):
        result = build_filenames("elonmusk", "123", ["video.mp4"])
        assert result == {"video.mp4": "@elonmusk_123.mp4"}

    def test_single_image(self):
        result = build_filenames("user", "456", ["photo.jpg"])
        assert result == {"photo.jpg": "@user_456.jpg"}

    def test_multiple_media(self):
        result = build_filenames("user", "789", ["a.jpg", "b.png", "c.mp4"])
        assert result == {
            "a.jpg": "@user_789_1.jpg",
            "b.png": "@user_789_2.png",
            "c.mp4": "@user_789_3.mp4",
        }

    def test_preserves_extension(self):
        result = build_filenames("user", "1", ["file.webm"])
        assert result == {"file.webm": "@user_1.webm"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 -m pytest tests/test_download.py::TestBuildFilenames -v`

Expected: FAIL — `ImportError: cannot import name 'build_filenames'`

- [ ] **Step 3: Implement build_filenames**

Add to `download.py` after `parse_tweet_url`:

```python
from pathlib import Path


def build_filenames(username: str, tweet_id: str, original_files: list[str]) -> dict[str, str]:
    """Map original filenames to @username_tweetID[_N].ext format.

    Returns dict of {original_name: new_name}.
    No index suffix for single files; _1, _2, etc. for multiple.
    """
    result = {}
    use_index = len(original_files) > 1
    for i, orig in enumerate(original_files, start=1):
        ext = Path(orig).suffix
        if use_index:
            new_name = f"@{username}_{tweet_id}_{i}{ext}"
        else:
            new_name = f"@{username}_{tweet_id}{ext}"
        result[orig] = new_name
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 -m pytest tests/test_download.py -v`

Expected: All 12 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add download.py tests/test_download.py
git commit -m "feat: add file naming logic with multi-media support"
```

---

### Task 4: Download function using yt-dlp

**Files:**
- Modify: `download.py` — add `download_media` function

- [ ] **Step 1: Implement download_media**

Add to `download.py`:

```python
import os
import tempfile
import shutil
import yt_dlp


SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
COOKIES_FILE = SCRIPT_DIR / "cookies.txt"


def download_media(url: str) -> list[str]:
    """Download all media from a tweet URL. Returns list of saved file paths."""
    username, tweet_id = parse_tweet_url(url)

    DOWNLOADS_DIR.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": os.path.join(tmpdir, "%(id)s_%(autonumber)s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": False,
            "no_warnings": False,
        }

        if COOKIES_FILE.exists():
            ydl_opts["cookiefile"] = str(COOKIES_FILE)
        else:
            print(f"Warning: {COOKIES_FILE} not found. Proceeding without auth.", file=sys.stderr)
            print("Some content (NSFW, private) may not be accessible.", file=sys.stderr)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Collect downloaded files
        downloaded = sorted(os.listdir(tmpdir))
        if not downloaded:
            print("Error: No media files were downloaded.", file=sys.stderr)
            sys.exit(1)

        # Rename and move to downloads/
        name_map = build_filenames(username, tweet_id, downloaded)
        saved_paths = []
        for orig, new_name in name_map.items():
            src = os.path.join(tmpdir, orig)
            dst = DOWNLOADS_DIR / new_name
            shutil.move(src, dst)
            saved_paths.append(str(dst))

    return saved_paths
```

- [ ] **Step 2: Manual smoke test with a real public tweet**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 -c "from download import download_media; print(download_media('https://x.com/NASA/status/1849966029939462468'))"`

Expected: File(s) downloaded to `downloads/` with correct naming.

- [ ] **Step 3: Commit**

```bash
git add download.py
git commit -m "feat: add download function with yt-dlp integration"
```

---

### Task 5: CLI entry point

**Files:**
- Modify: `download.py` — add `main()` and `if __name__` block

- [ ] **Step 1: Add CLI entry point**

Add to bottom of `download.py`:

```python
def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <tweet_url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    try:
        parse_tweet_url(url)  # validate early
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    saved = download_media(url)
    for path in saved:
        print(path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test CLI with no args**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 download.py 2>&1; echo "Exit: $?"`

Expected:
```
Usage: python download.py <tweet_url>
Exit: 1
```

- [ ] **Step 3: Test CLI with invalid URL**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 download.py "https://youtube.com/watch?v=123" 2>&1; echo "Exit: $?"`

Expected:
```
Error: Not a valid X/Twitter URL: https://youtube.com/watch?v=123
Exit: 1
```

- [ ] **Step 4: Test CLI with a real tweet URL**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 download.py "https://x.com/NASA/status/1849966029939462468"`

Expected: Downloads file(s), prints path(s) to stdout.

- [ ] **Step 5: Run full test suite**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 -m pytest tests/ -v`

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add download.py
git commit -m "feat: add CLI entry point with usage and error handling"
```

---

### Task 6: Final integration test and cleanup

**Files:**
- Review: all files for consistency

- [ ] **Step 1: Verify complete file structure**

Run: `ls -la "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot/"`

Expected:
```
download.py
requirements.txt
.gitignore
downloads/
tests/
docs/
```

- [ ] **Step 2: Run full test suite one final time**

Run: `cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot" && python3 -m pytest tests/ -v`

Expected: All tests PASS.

- [ ] **Step 3: End-to-end test with a video tweet**

Find a public tweet with video and run:
```bash
cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot"
python3 download.py "<video_tweet_url>"
ls -la downloads/
```

Expected: Video file downloaded with correct `@username_ID.mp4` naming.

- [ ] **Step 4: End-to-end test with an image tweet**

Find a public tweet with image(s) and run:
```bash
cd "/Users/admin/Library/CloudStorage/GoogleDrive-yevhen.hrushko@gmail.com/Мой диск/Projects/telegram-downloader-bot"
python3 download.py "<image_tweet_url>"
ls -la downloads/
```

Expected: Image file(s) downloaded with correct naming.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: finalize project structure"
```
