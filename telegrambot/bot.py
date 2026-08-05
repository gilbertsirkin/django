"""
python-telegram-bot Application for the WolvCapital Telegram bot.

This runs in WEBHOOK mode, not polling — Telegram POSTs each update to our
Django view (see views.py), which hands it to `application.process_update()`.
The Application is built once per process (per gunicorn worker) and reused
across requests.
"""
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger("telegrambot")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# URL of the Mini App / web dashboard the "Open App" button should launch.
# Must be https:// — Telegram will reject webapp buttons pointing at http.
TELEGRAM_MINIAPP_URL = os.environ.get("TELEGRAM_MINIAPP_URL", "")


def _build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot handlers will not function")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN or "unset").build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    return app


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = None
    if TELEGRAM_MINIAPP_URL:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Open App", web_app=WebAppInfo(url=TELEGRAM_MINIAPP_URL))]]
        )
    await update.message.reply_text(
        "Welcome to WolvCapital 👋\n\n"
        "Tap \"Open App\" below to view your dashboard, or use /help to see "
        "what I can do.",
        reply_markup=keyboard,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\n"
        "/start — welcome message + open the app\n"
        "/help — this message"
    )


# Built once at import time, reused across requests within this worker process.
application = _build_application()
