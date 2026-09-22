# Win-back campaign email templates

This directory contains **six drafts**: three campaign tracks, each with an HTML and plain-text version.

- `account-maturity.html` and `.txt`: maturity and activity notification.
- `feature-updates.html` and `.txt`: verified protocol and feature updates.
- `security-checkin.html` and `.txt`: security and compliance check-in.

The maturity track is now wired to `python manage.py maturity_winback --send` and added to the daily Railway schedule at 01:30 UTC. Sending remains disabled until the deployment environment sets `MATURITY_WINBACK_ENABLED=true`.

## Existing backend integration

The repository already has `core/services/email_service.py`, which renders paired templates from `templates/emails/<template_name>.html` and `.txt` through `EmailMultiAlternatives`. The existing investment maturity command is `investments/management/commands/complete_expired_plans.py`; it currently sends the existing `investment_completed` notification rather than these win-back drafts.

When wiring these drafts into a campaign task, pass the recipient as `user`, and provide the following context values explicitly:

- Common: `company_name`, `dashboard_url`, `support_url`, `preferences_url`, `unsubscribe_url`, and `company_address`.
- Maturity: `maturity.plan_name`, `maturity.maturity_date`, `maturity.principal`, `maturity.accrued_yield`, `maturity.total_balance`, `maturity.currency`, `maturity.rollover_url`, and `maturity.withdraw_url`.
- Feature updates: an approved `updates` list containing `title`, `summary`, and optional `url`.
- Security: `security.action_name`, `security.action_summary`, and `security.action_url`.

The command applies a 30-day inactivity threshold, requires an active account, verified email, enabled master notifications, and enabled investment emails. It records one delivery ledger row per completed investment, supports `--dry-run`, and refuses to send unless `MATURITY_WINBACK_ENABLED=true`. The existing email service supplies `brand_name`, `support_email`, and `site_url`; the command maps the remaining branded context values.

Run `python manage.py maturity_winback --dry-run` first. Use `--limit` for a controlled rollout. The Railway cron invokes `--send`, but the feature flag is deliberately off until the dry-run recipient count and list have been reviewed.

Do not populate the feature-update template with unverified claims about audits, DEX listings, yields, withdrawals, or compliance. Do not send maturity figures unless they are read from the authoritative investment records.
