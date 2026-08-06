"""
Outbound Telegram push notifications for linked user accounts.

Uses the same python-telegram-bot Application (and thus the same bot token)
as the webhook handler in views.py — one Application instance per worker
process, reused for both inbound updates and outbound sends.
"""
import logging

from asgiref.sync import async_to_sync
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, TelegramError

from .bot import application

logger = logging.getLogger("telegrambot")

_initialized = False


async def _ensure_initialized() -> None:
    global _initialized
    if not _initialized:
        await application.initialize()
        _initialized = True


async def _send(chat_id: int, text: str, reply_markup=None) -> bool:
    await _ensure_initialized()
    try:
        await application.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
        return True
    except Forbidden:
        logger.info("telegrambot: user %s has blocked the bot, cannot notify", chat_id)
        return False
    except TelegramError:
        logger.exception("telegrambot: failed to send message to chat_id=%s", chat_id)
        return False


def send_telegram_notification(chat_id: int, text: str, reply_markup=None) -> bool:
    """Synchronous entry point — safe to call from regular Django code/management commands."""
    if not chat_id:
        return False
    return async_to_sync(_send)(chat_id, text, reply_markup)


def notify_profile(profile, text: str, reply_markup=None) -> bool:
    """
    Send a notification to a users.models.Profile, respecting their
    telegram_notifications_enabled toggle. Returns False (no-op) if the
    profile has no linked chat_id or has notifications disabled.
    """
    if not profile or not profile.telegram_chat_id or not profile.telegram_notifications_enabled:
        return False

    return send_telegram_notification(profile.telegram_chat_id, text, reply_markup)


def roi_payout_keyboard(miniapp_url):
    if not miniapp_url:
        return None
    from telegram import WebAppInfo

    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("View Dashboard", web_app=WebAppInfo(url=miniapp_url))]]
    )
