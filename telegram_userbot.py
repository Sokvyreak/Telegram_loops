#!/usr/bin/env python3
"""
telegram_userbot.py

Runs on YOUR personal Telegram account (not a separate bot account) using
the Telethon library. Listens for a command pattern you type in any chat
(including "Saved Messages" — a chat with yourself) and replies with the
compiled C++ program's output.

Setup:
  1. pip install telethon --break-system-packages
  2. Get API credentials from https://my.telegram.org (see instructions below)
  3. Fill in API_ID and API_HASH below
  4. First run will ask for your phone number + login code (one-time setup)
  5. Make sure g++ and test.cpp are set up as before

Usage (type these in any chat, e.g. "Saved Messages"):
  .count           -> counts 0 to 1000
  .count 20        -> counts 0 to 20
  .count 5 15      -> counts 5 to 15

Note: This uses your real account, not a bot. Keep API_ID/API_HASH and the
generated session file private — they grant access to your account.
"""

import os
import subprocess
import tempfile

from telethon import TelegramClient, events

# ---------------------------------------------------------------------------
# Configuration — get these from https://my.telegram.org
# (log in with your phone number -> API development tools -> create an app)
# ---------------------------------------------------------------------------
API_ID = 31133428
  # Replace with your numeric API ID
API_HASH = "026578a57b7a99699a4d0ff47d35de76"

CPP_FILE = "test.cpp"
MAX_RANGE = 5000
TELEGRAM_MESSAGE_LIMIT = 4000

# The session file stores your login so you don't have to re-enter the code
# every time. Treat it like a password — don't share this file.
SESSION_NAME = "userbot_session"


def compile_and_run(cpp_path: str, program_args: list) -> tuple:
    if not os.path.exists(cpp_path):
        return False, f"Couldn't find {cpp_path} — make sure it's in the same folder as this script."

    with tempfile.TemporaryDirectory() as tmp_dir:
        exe_path = os.path.join(tmp_dir, "program.exe")

        compile_result = subprocess.run(
            ["g++", cpp_path, "-o", exe_path],
            capture_output=True, text=True, timeout=15,
        )
        if compile_result.returncode != 0:
            return False, f"Compile error:\n{compile_result.stderr[:1500]}"

        try:
            run_result = subprocess.run(
                [exe_path] + program_args,
                capture_output=True, text=True, timeout=10,
            )
        except subprocess.TimeoutExpired:
            return False, "Program timed out after 10 seconds (possible infinite loop)."

        if run_result.returncode != 0:
            error_msg = run_result.stderr or run_result.stdout
            return False, f"Program exited with an error:\n{error_msg[:1500]}"

        return True, run_result.stdout


client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


# outgoing=True means: only trigger on messages YOU send (not messages sent
# to you) — so typing ".count" in any chat triggers it, without responding
# to other people typing the same thing.
@client.on(events.NewMessage(outgoing=True, pattern=r'^\.count(?:\s+(-?\d+))?(?:\s+(-?\d+))?$'))
async def count_handler(event):
    raw_args = [g for g in event.pattern_match.groups() if g is not None]

    if len(raw_args) == 2:
        start_val, end_val = int(raw_args[0]), int(raw_args[1])
        if end_val - start_val > MAX_RANGE:
            await event.reply(f"Range too large — keep it under {MAX_RANGE} numbers.")
            return
    elif len(raw_args) == 1:
        if int(raw_args[0]) > MAX_RANGE:
            await event.reply(f"Range too large — keep it under {MAX_RANGE} numbers.")
            return

    await event.reply("Compiling and running, one sec...")

    success, output = compile_and_run(CPP_FILE, raw_args)

    if not success:
        await event.reply(f"Error: {output}")
        return

    if not output.strip():
        await event.reply("Program ran successfully but printed no output.")
        return

    if len(output) <= TELEGRAM_MESSAGE_LIMIT:
        await event.reply(f"Output:\n{output}")
    else:
        for i in range(0, len(output), TELEGRAM_MESSAGE_LIMIT):
            await event.reply(output[i:i + TELEGRAM_MESSAGE_LIMIT])


def main():
    if API_ID == 0 or API_HASH == "PASTE_YOUR_API_HASH_HERE":
        print("ERROR: Set your API_ID and API_HASH first (get them from https://my.telegram.org).")
        return

    print("Starting userbot. On first run, you'll be asked for your phone number and login code.")
    with client:
        print("Userbot is running. Type '.count' in any chat (e.g. Saved Messages) to test.")
        client.run_until_disconnected()


if __name__ == "__main__":
    main()
