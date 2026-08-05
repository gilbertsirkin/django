from django.urls import path

from .views import telegram_bot_webhook

urlpatterns = [
    path("webhook/", telegram_bot_webhook, name="telegram_bot_webhook"),
]
