#!/usr/bin/env python3
"""
telegram_cpp_bot.py

A Telegram bot that compiles and runs a local C++ file when triggered
by the /count command, then sends the program's output back as a message.

Setup:
  1. pip install python-telegram-bot --break-system-packages
  2. Get a bot token from @BotFather on Telegram (see instructions below)
  3. Set your token in the BOT_TOKEN variable, or as an environment variable
  4. Make sure g++ is installed and on your PATH (you already set this up)
  5. Put test.cpp in the same folder as this script (or update CPP_FILE path)
  6. Run: python telegram_cpp_bot.py

How it works:
  - /count -> compiles test.cpp with g++, runs the resulting exe, sends output
  - /start -> shows a welcome message with available commands
"""

import os
import subprocess
import tempfile
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Get this from @BotFather (see setup instructions in the chat response).
# You can hardcode it here for local testing, or set it as an environment
# variable instead (safer — avoids leaving your token in a saved file):
#   PowerShell:  $env:TELEGRAM_BOT_TOKEN = "your-token-here"
BOT_TOKEN = os#!/usr/bin/env python3
"""
telegram_cpp_bot.py

A Telegram bot that compiles and runs a local C++ file when triggered
by the /count command, then sends the program's output back as a message.

Setup:
  1. pip install python-telegram-bot --break-system-packages
  2. Get a bot token from @BotFather on Telegram (see instructions below)
  3. Set your token in the BOT_TOKEN variable, or as an environment variable
  4. Make sure g++ is installed and on your PATH (you already set this up)
  5. Put test.cpp in the same folder as this script (or update CPP_FILE path)
  6. Run: python telegram_cpp_bot.py

How it works:
  - /count -> compiles test.cpp with g++, runs the resulting exe, sends output
  - /start -> shows a welcome message with available commands
"""

import os
import subprocess
import tempfile
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Get this from @BotFather (see setup instructions in the chat response).
# You can hardcode it here for local testing, or set it as an environment
# variable instead (safer — avoids leaving your token in a saved file):
#   PowerShell:  $env:TELEGRAM_BOT_TOKEN = "your-token-here"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")

# Path to your C++ source file
CPP_FILE = "test.cpp"

# Max characters Telegram allows in one message
TELEGRAM_MESSAGE_LIMIT = 4000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Compile + run helper
# ---------------------------------------------------------------------------

def compile_and_run(cpp_path: str, program_args: list[str] | None = None) -> tuple[bool, str]:
    """
    Compiles the given C++ file and runs it with optional command-line arguments.
    Returns (success, output_or_error_message).
    """
    if program_args is None:
        program_args = []

    if not os.path.exists(cpp_path):
        return False, f"Couldn't find {cpp_path} — make sure it's in the same folder as this bot script."

    with tempfile.TemporaryDirectory() as tmp_dir:
        exe_path = os.path.join(tmp_dir, "program.exe")

        # Compile
        compile_result = subprocess.run(
            ["g++", cpp_path, "-o", exe_path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if compile_result.returncode != 0:
            return False, f"Compile error:\n{compile_result.stderr[:1500]}"

        # Run (with a timeout so a stray infinite loop can't hang the bot forever)
        try:
            run_result = subprocess.run(
                [exe_path] + program_args,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            return False, "Program timed out after 10 seconds (possible infinite loop)."

        if run_result.returncode != 0:
            error_msg = run_result.stderr or run_result.stdout
            return False, f"Program exited with an error:\n{error_msg[:1500]}"

        return True, run_result.stdout


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I can compile and run test.cpp for you.\n\n"
        "Commands:\n"
        "/count - counts from 0 to 100 (default)\n"
        "/count <end> - counts from 0 to <end>\n"
        "/count <start> <end> - counts from <start> to <end>\n\n"
        "Example: /count 5 20"
    )


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # context.args contains whatever the user typed after /count, split by spaces.
    # e.g. "/count 5 20" -> context.args == ["5", "20"]
    raw_args = context.args or []

    # Validate: only allow up to 2 numeric arguments, reject anything else.
    if len(raw_args) > 2:
        await update.message.reply_text("Too many arguments. Use: /count [start] [end]")
        return

    for arg in raw_args:
        if not arg.lstrip("-").isdigit():
            await update.message.reply_text(f"'{arg}' isn't a valid number. Use: /count [start] [end]")
            return

    # Guardrail: keep ranges reasonable so nobody accidentally asks for
    # millions of lines of output that would flood the chat.
    MAX_RANGE = 5000
    if len(raw_args) == 2:
        start_val, end_val = int(raw_args[0]), int(raw_args[1])
        if end_val - start_val > MAX_RANGE:
            await update.message.reply_text(f"Range too large — please keep it under {MAX_RANGE} numbers.")
            return
    elif len(raw_args) == 1:
        end_val = int(raw_args[0])
        if end_val > MAX_RANGE:
            await update.message.reply_text(f"Range too large — please keep it under {MAX_RANGE} numbers.")
            return

    await update.message.reply_text("Compiling and running, one sec...")

    success, output = compile_and_run(CPP_FILE, program_args=raw_args)

    if not success:
        await update.message.reply_text(f"⚠️ {output}")
        return

    if not output.strip():
        await update.message.reply_text("Program ran successfully but printed no output.")
        return

    # Telegram messages have a length limit — split into chunks if needed
    if len(output) <= TELEGRAM_MESSAGE_LIMIT:
        await update.message.reply_text(f"Output:\n{output}")
    else:
        for i in range(0, len(output), TELEGRAM_MESSAGE_LIMIT):
            chunk = output[i:i + TELEGRAM_MESSAGE_LIMIT]
            await update.message.reply_text(chunk)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        print("ERROR: Set your bot token first (see BOT_TOKEN in this file, or")
        print("set the TELEGRAM_BOT_TOKEN environment variable).")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("count", count))

    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main().environ.get("TELEGRAM_BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")

# Path to your C++ source file
CPP_FILE = "test.cpp"

# Max characters Telegram allows in one message
TELEGRAM_MESSAGE_LIMIT = 4000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Compile + run helper
# ---------------------------------------------------------------------------

def compile_and_run(cpp_path: str) -> tuple[bool, str]:
    """
    Compiles the given C++ file and runs it.
    Returns (success, output_or_error_message).
    """
    if not os.path.exists(cpp_path):
        return False, f"Couldn't find {cpp_path} — make sure it's in the same folder as this bot script."

    with tempfile.TemporaryDirectory() as tmp_dir:
        exe_path = os.path.join(tmp_dir, "program.exe")

        # Compile
        compile_result = subprocess.run(
            ["g++", cpp_path, "-o", exe_path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if compile_result.returncode != 0:
            return False, f"Compile error:\n{compile_result.stderr[:1500]}"

        # Run (with a timeout so a stray infinite loop can't hang the bot forever)
        try:
            run_result = subprocess.run(
                [exe_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            return False, "Program timed out after 10 seconds (possible infinite loop)."

        if run_result.returncode != 0:
            return False, f"Program exited with an error:\n{run_result.stderr[:1500]}"

        return True, run_result.stdout


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I can compile and run test.cpp for you.\n\n"
        "Commands:\n"
        "/count - compiles and runs test.cpp, sends the output"
    )


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Compiling and running, one sec...")

    success, output = compile_and_run(CPP_FILE)

    if not success:
        await update.message.reply_text(f"⚠️ {output}")
        return

    if not output.strip():
        await update.message.reply_text("Program ran successfully but printed no output.")
        return

    # Telegram messages have a length limit — split into chunks if needed
    if len(output) <= TELEGRAM_MESSAGE_LIMIT:
        await update.message.reply_text(f"Output:\n{output}")
    else:
        for i in range(0, len(output), TELEGRAM_MESSAGE_LIMIT):
            chunk = output[i:i + TELEGRAM_MESSAGE_LIMIT]
            await update.message.reply_text(chunk)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        print("ERROR: Set your bot token first (see BOT_TOKEN in this file, or")
        print("set the TELEGRAM_BOT_TOKEN environment variable).")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("count", count))

    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
