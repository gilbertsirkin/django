import json
import logging
import os

from asgiref.sync import async_to_sync
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from telegram import Update

from .bot import application

logger = logging.getLogger("telegrambot")

# Optional but recommended: set this in your env and pass it as `secret_token`
# to Telegram's setWebhook call. Telegram then sends it back on every request
# in the X-Telegram-Bot-Api-Secret-Token header, so we can reject spoofed hits.
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")

_initialized = False


async def _process(update: Update) -> None:
    global _initialized
    if not _initialized:
        await application.initialize()
        _initialized = True
    await application.process_update(update)


@csrf_exempt
@require_POST
def telegram_bot_webhook(request):
    if TELEGRAM_WEBHOOK_SECRET:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header != TELEGRAM_WEBHOOK_SECRET:
            logger.warning("telegrambot: rejected webhook call with bad/missing secret token")
            return HttpResponse(status=403)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    update = Update.de_json(data, application.bot)

    try:
        async_to_sync(_process)(update)
    except Exception:
        logger.exception("telegrambot: error processing update")
        # Still return 200 — returning an error to Telegram just triggers
        # retries of the same update, which usually makes things worse.

    return JsonResponse({"ok": True})
