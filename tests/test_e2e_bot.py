#!/usr/bin/env python3
"""End-to-end tests for the Telegram bot. Sends real URLs and verifies responses.

Usage: ./venv/bin/python tests/test_e2e_bot.py

Requires:
  - telegram.session (run setup_telegram.py first)
  - Bot must be running and accessible
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

SCRIPT_DIR = Path(__file__).parent.parent
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID", "34456187"))
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "f451a6ed6c0b0f596bdbb7a5f3938440")
TELEGRAM_SESSION = str(SCRIPT_DIR / "telegram")
BOT_USERNAME = "yh_downloader_bot"

# Test URLs — real public content
TEST_CASES = [
    {
        "name": "Twitter image",
        "url": "https://x.com/FermusP/status/2040698457007001753/photo/1",
        "expect": "document",  # sent as document
    },
    {
        "name": "Twitter video",
        "url": "https://x.com/i/status/2040652343121731860",
        "expect": "document",
    },
    {
        "name": "Instagram video",
        "url": "https://www.instagram.com/p/DVJY_24jRqs/",
        "expect": "document",
    },
    {
        "name": "Telegram single message (image)",
        "url": "https://t.me/c/2161704047/739",
        "expect": "document",
    },
]

TIMEOUT = 120  # seconds to wait for bot response


async def run_tests():
    client = TelegramClient(TELEGRAM_SESSION, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start()

    bot_entity = await client.get_entity(BOT_USERNAME)
    print(f"Connected. Testing bot @{BOT_USERNAME}\n")

    passed = 0
    failed = 0

    for i, test in enumerate(TEST_CASES, 1):
        name = test["name"]
        url = test["url"]
        print(f"[{i}/{len(TEST_CASES)}] {name}")
        print(f"  Sending: {url}")

        # Send URL to bot
        await client.send_message(bot_entity, url)

        # Wait for response(s) — bot sends status messages then media
        start = time.time()
        got_media = False
        last_text = ""

        while time.time() - start < TIMEOUT:
            await asyncio.sleep(3)
            messages = await client.get_messages(bot_entity, limit=5)

            for msg in messages:
                # Skip our own messages
                if msg.out:
                    continue
                # Check for media (document = our expected format)
                if msg.document or msg.photo:
                    got_media = True
                    if msg.document:
                        size = msg.document.size
                        mime = msg.document.mime_type
                        print(f"  Received: document ({mime}, {size / 1024:.1f} KB)")
                    elif msg.photo:
                        print(f"  Received: photo")
                    break
                # Check for text responses
                if msg.text and msg.text != last_text:
                    last_text = msg.text
                    if "Download failed" in msg.text or "unexpected error" in msg.text.lower():
                        print(f"  FAILED: {msg.text}")
                        break
                    elif "Downloading" in msg.text or "Done:" in msg.text:
                        print(f"  Status: {msg.text}")

            if got_media or "Download failed" in last_text or "unexpected error" in last_text.lower():
                break

        if got_media:
            print(f"  PASS\n")
            passed += 1
        else:
            print(f"  FAIL — no media received (last: {last_text})\n")
            failed += 1

        # Wait between tests to avoid rate limiting
        if i < len(TEST_CASES):
            await asyncio.sleep(5)

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed out of {len(TEST_CASES)}")

    await client.disconnect()
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
