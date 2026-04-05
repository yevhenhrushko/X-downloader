#!/usr/bin/env python3
"""One-time Telegram login. Creates telegram.session file for future use."""

import os
from pathlib import Path
from telethon.sync import TelegramClient

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SESSION_FILE = str(SCRIPT_DIR / "telegram")

API_ID = 34456187
API_HASH = "f451a6ed6c0b0f596bdbb7a5f3938440"

print("Telegram Login Setup")
print("=" * 40)
print("This will create a session file for downloading media.")
print("You'll receive a code in your Telegram app.\n")

with TelegramClient(SESSION_FILE, API_ID, API_HASH) as client:
    print(f"\nLogged in as: {client.get_me().first_name}")
    print(f"Session saved to: {SESSION_FILE}.session")
    print("\nDone! You can now download from private Telegram channels.")
