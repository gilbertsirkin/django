"""
python-telegram-bot Application for the WolvCapital Telegram bot.

Runs in WEBHOOK mode — Telegram POSTs each update to our Django view
(see views.py), which hands it to `application.process_update()`.
The Application is built once per process (per gunicorn worker) and reused
across requests, and reused again by notify.py for outbound pushes.
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
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("roi", roi_command))
    app.add_handler(CommandHandler("unlink", unlink_command))
    return app


def _open_app_keyboard():
    if not TELEGRAM_MINIAPP_URL:
        return None
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Open App", web_app=WebAppInfo(url=TELEGRAM_MINIAPP_URL))]]
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles both plain /start and deep-linked /start <token>.
    The token comes from a "Connect Telegram" button in the dashboard
    (users.services.generate_telegram_link_token) and is consumed here to
    link this chat_id to the user's account.
    """
    from asgiref.sync import sync_to_async

    from users.services import consume_telegram_link_token

    args = context.args or []
    token = args[0] if args else None

    if token:
        chat = update.effective_chat
        tg_user = update.effective_user
        username = f"@{tg_user.username}" if tg_user and tg_user.username else None

        profile = await sync_to_async(consume_telegram_link_token)(
            token, chat.id, username
        )

        if profile:
            await update.message.reply_text(
                f"✅ Linked to {profile.user.email}\n\n"
                "You'll now get payout and account notifications here. "
                "Try /balance, /stats, or /roi.",
                reply_markup=_open_app_keyboard(),
            )
            return
        else:
            await update.message.reply_text(
                "⚠️ That link has expired or was already used. Head back to "
                "your dashboard and tap \"Connect Telegram\" again to get a "
                "fresh link."
            )
            return

    await update.message.reply_text(
        "Welcome to WolvCapital 👋\n\n"
        "Tap \"Open App\" below to view your dashboard, or use /help to see "
        "what I can do.\n\n"
        "To get account notifications and use /balance, /stats, and /roi "
        "here, connect your account from the dashboard's Settings page.",
        reply_markup=_open_app_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\n"
        "/start — welcome message + open the app\n"
        "/help — this message\n"
        "/balance — your current wallet balance\n"
        "/stats — investment portfolio summary\n"
        "/roi — recent ROI payouts\n"
        "/unlink — disconnect this Telegram account\n\n"
        "/balance, /stats, and /roi require your account to be connected "
        "first — see the Settings page on your dashboard."
    )


async def _get_linked_profile(update: Update):
    from asgiref.sync import sync_to_async

    from users.services import get_profile_by_telegram_chat_id

    chat_id = update.effective_chat.id
    return await sync_to_async(get_profile_by_telegram_chat_id)(chat_id)


_NOT_LINKED_TEXT = (
    "🔒 This Telegram account isn't connected yet.\n\n"
    "Go to your dashboard → Settings → \"Connect Telegram\" to link it."
)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from asgiref.sync import sync_to_async

    profile = await _get_linked_profile(update)
    if not profile:
        await update.message.reply_text(_NOT_LINKED_TEXT)
        return

    def _fetch_balance():
        from users.models import UserWallet

        wallet = UserWallet.objects.filter(user=profile.user).first()
        return wallet.balance if wallet else None

    balance = await sync_to_async(_fetch_balance)()
    if balance is None:
        await update.message.reply_text("No wallet found on your account yet.")
        return

    await update.message.reply_text(f"💰 Wallet balance: <b>${balance:,.2f}</b>", parse_mode="HTML")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from asgiref.sync import sync_to_async

    profile = await _get_linked_profile(update)
    if not profile:
        await update.message.reply_text(_NOT_LINKED_TEXT)
        return

    def _fetch_stats():
        from django.db.models import Sum

        from investments.models import UserInvestment

        qs = UserInvestment.objects.filter(user=profile.user)
        active = qs.filter(status__in=[UserInvestment.STATUS_APPROVED, UserInvestment.STATUS_ACTIVE])
        completed = qs.filter(status=UserInvestment.STATUS_COMPLETED)

        active_total = active.aggregate(total=Sum("amount"))["total"] or 0
        completed_total = completed.aggregate(total=Sum("amount"))["total"] or 0
        active_count = active.count()

        return active_count, active_total, completed_total, completed.count()

    active_count, active_total, completed_total, completed_count = await sync_to_async(_fetch_stats)()

    await update.message.reply_text(
        "📊 <b>Portfolio Summary</b>\n\n"
        f"Active investments: {active_count} (${active_total:,.2f})\n"
        f"Completed investments: {completed_count} (${completed_total:,.2f})",
        parse_mode="HTML",
    )


async def roi_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from asgiref.sync import sync_to_async

    profile = await _get_linked_profile(update)
    if not profile:
        await update.message.reply_text(_NOT_LINKED_TEXT)
        return

    def _fetch_recent_payouts():
        from investments.models import DailyRoiPayout

        return list(
            DailyRoiPayout.objects.filter(investment__user=profile.user)
            .select_related("investment", "investment__plan")
            .order_by("-payout_date")[:5]
        )

    payouts = await sync_to_async(_fetch_recent_payouts)()

    if not payouts:
        await update.message.reply_text("No ROI payouts recorded yet.")
        return

    lines = ["📈 <b>Recent ROI Payouts</b>\n"]
    for p in payouts:
        plan_name = p.investment.plan.name if p.investment and p.investment.plan else "Investment"
        lines.append(f"{p.payout_date} — ${p.amount:,.2f} ({plan_name})")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from asgiref.sync import sync_to_async

    from users.services import unlink_telegram

    chat_id = update.effective_chat.id
    unlinked = await sync_to_async(unlink_telegram)(chat_id)

    if unlinked:
        await update.message.reply_text("Your Telegram account has been disconnected.")
    else:
        await update.message.reply_text("This Telegram account wasn't connected to anything.")


# Built once at import time, reused across requests within this worker process.
application = _build_application()
