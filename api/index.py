import os

from django.core.management import call_command

from wolvcapital.wsgi import application as app

if os.environ.get("RUN_MIGRATIONS_ON_BOOT") == "1":
    try:
        call_command("migrate", interactive=False)
    except Exception as exc:
        # Don't crash cold starts if a migration fails — log it via print
        # since this runs before Django's logging may be fully configured,
        # and check Vercel runtime logs if something looks off after deploy.
        print(f"⚠️ migrate on boot failed: {exc}")
