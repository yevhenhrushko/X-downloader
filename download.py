#!/usr/bin/env python3
"""Download videos and images from X/Twitter in best quality."""

import re
import sys
from pathlib import Path


def parse_tweet_url(url: str) -> tuple[str, str]:
    """Extract (username, tweet_id) from an X/Twitter URL.

    Raises ValueError if URL doesn't match expected pattern.
    """
    pattern = r"https?://(?:mobile\.)?(?:x\.com|twitter\.com)/([^/]+)/status/(\d+)"
    match = re.match(pattern, url.strip().rstrip("/"))
    if not match:
        raise ValueError(f"Not a valid X/Twitter URL: {url}")
    return match.group(1), match.group(2)


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
