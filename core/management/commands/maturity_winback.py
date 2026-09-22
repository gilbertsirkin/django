"""Send one maturity win-back email per completed investment to eligible inactive users.

Examples:
    python manage.py maturity_winback --dry-run
    python manage.py maturity_winback --send
    python manage.py maturity_winback --send --limit 25

The scheduled job should call ``--send`` only after the first dry-run count has
been reviewed. The command never sends to unverified addresses, users who have
not opted into investment emails, or investments already present in the ledger.
"""

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from core.email_service import EmailService
from core.models import MaturityWinbackDelivery
from investments.models import DailyRoiPayout, UserInvestment


class Command(BaseCommand):
    help = "Send account maturity win-back emails to eligible inactive users."

    def add_arguments(self, parser):
        parser.add_argument("--send", action="store_true", help="Actually send eligible emails.")
        parser.add_argument("--dry-run", action="store_true", help="List eligible recipients without sending.")
        parser.add_argument("--limit", type=int, default=0, help="Limit eligible investments for a controlled rollout.")
        parser.add_argument("--inactive-days", type=int, default=30, help="Required days since the user's last login/activity.")

    def handle(self, *args, **options):
        if options["send"] and options["dry_run"]:
            self.stderr.write(self.style.ERROR("Choose either --send or --dry-run, not both."))
            return
        send = bool(options["send"])
        if send and not getattr(settings, "MATURITY_WINBACK_ENABLED", False):
            self.stderr.write(
                self.style.ERROR(
                    "Maturity win-back is disabled. Set MATURITY_WINBACK_ENABLED=true "
                    "only after reviewing a dry run and approving the recipient scope."
                )
            )
            return
        inactive_days = max(1, options["inactive_days"])
        cutoff = timezone.now() - timedelta(days=inactive_days)
        qs = self._eligible_queryset(cutoff)
        if options["limit"]:
            qs = qs[: options["limit"]]
        eligible = [investment for investment in qs if self._is_inactive(investment.user, cutoff)]
        self.stdout.write(f"Eligible maturity win-back investments: {len(eligible)}")
        for investment in eligible:
            user = investment.user
            self.stdout.write(
                f"{'[SEND]' if send else '[DRY RUN]'} {investment.id} -> {user.email} "
                f"({investment.plan.name}, maturity {investment.ends_at:%Y-%m-%d})"
            )
        if not send:
            self.stdout.write(self.style.WARNING("No email was sent. Use --send only after reviewing this recipient list."))
            return

        sent = failed = skipped = 0
        for investment in eligible:
            result = self._send_one(investment, cutoff)
            if result == "sent":
                sent += 1
            elif result == "skipped":
                skipped += 1
            else:
                failed += 1
        self.stdout.write(self.style.SUCCESS(f"Maturity win-back complete: sent={sent}, failed={failed}, skipped={skipped}"))

    def _eligible_queryset(self, cutoff):
        return (
            UserInvestment.objects.filter(
                status=UserInvestment.STATUS_COMPLETED,
                ends_at__isnull=False,
                ends_at__lte=timezone.now(),
                user__is_active=True,
                user__email__isnull=False,
                user__profile__email_notifications_enabled=True,
                user__profile__email_investments=True,
                user__profile__email_verified=True,
            )
            .exclude(maturity_winback_delivery__isnull=False)
            .select_related("user", "user__profile", "plan")
            .prefetch_related(
                Prefetch(
                    "dailyroipayout_set",
                    queryset=DailyRoiPayout.objects.filter(credited_at__isnull=False),
                    to_attr="credited_roi_payouts",
                )
            )
            .order_by("ends_at", "id")
        )

    def _last_activity(self, user):
        latest_event = user.activity_events.order_by("-visited_at").first()
        return max(
            [value for value in (getattr(user, "last_login", None), getattr(latest_event, "visited_at", None)) if value],
            default=None,
        )

    def _is_inactive(self, user, cutoff):
        last_activity = self._last_activity(user)
        return not last_activity or last_activity <= cutoff

    def _send_one(self, investment, cutoff):
        user = investment.user
        if not self._is_inactive(user, cutoff):
            return "skipped"
        if MaturityWinbackDelivery.objects.filter(investment=investment).exists():
            return "skipped"

        credited_yield = sum(
            (payout.amount for payout in getattr(investment, "credited_roi_payouts", [])),
            Decimal("0.00"),
        )
        total_balance = (investment.amount + credited_yield).quantize(Decimal("0.01"))
        subject = f"Your {investment.plan.name} term has matured - {EmailService.BRAND_NAME}"
        base_url = getattr(settings, "PUBLIC_SITE_URL", getattr(settings, "SITE_URL", "https://www.wolvcapital.com")).rstrip("/")
        context = {
            "user": user,
            "company_name": EmailService.BRAND_NAME,
            "company_address": getattr(settings, "COMPANY_ADDRESS", "WolvCapital"),
            "dashboard_url": f"{base_url}/dashboard",
            "support_url": f"{base_url}/contact",
            "preferences_url": f"{base_url}/profile/email-preferences/",
            "unsubscribe_url": f"{base_url}/profile/email-preferences/",
            "maturity": {
                "plan_name": investment.plan.name,
                "maturity_date": investment.ends_at.date().isoformat(),
                "principal": f"{investment.amount:.2f}",
                "accrued_yield": f"{credited_yield:.2f}",
                "total_balance": f"{total_balance:.2f}",
                "currency": "USDT",
                "rollover_url": f"{base_url}/dashboard/new-investment",
                "withdraw_url": f"{base_url}/dashboard/withdraw",
            },
        }
        try:
            with transaction.atomic():
                delivery, created = MaturityWinbackDelivery.objects.get_or_create(
                    investment=investment,
                    defaults={"recipient_email": user.email, "subject": subject},
                )
                if not created:
                    return "skipped"
                sent = EmailService.send_template(
                    "account-maturity",
                    user.email,
                    context=context,
                    subject=subject,
                )
                if not sent:
                    delivery.delete()
                    return "failed"
                return "sent"
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Failed for investment {investment.id}: {exc}"))
            return "failed"
