# Win-back campaign email templates

This directory contains **six drafts**: three campaign tracks, each with an HTML and plain-text version.

- `account-maturity.html` and `.txt`: maturity and activity notification.
- `feature-updates.html` and `.txt`: verified protocol and feature updates.
- `security-checkin.html` and `.txt`: security and compliance check-in.

The templates are drafts only. They do not activate sending or change the existing cron/management-command behavior.

## Existing backend integration

The repository already has `core/services/email_service.py`, which renders paired templates from `templates/emails/<template_name>.html` and `.txt` through `EmailMultiAlternatives`. The existing investment maturity command is `investments/management/commands/complete_expired_plans.py`; it currently sends the existing `investment_completed` notification rather than these win-back drafts.

When wiring these drafts into a campaign task, pass the recipient as `user`, and provide the following context values explicitly:

- Common: `company_name`, `dashboard_url`, `support_url`, `preferences_url`, `unsubscribe_url`, and `company_address`.
- Maturity: `maturity.plan_name`, `maturity.maturity_date`, `maturity.principal`, `maturity.accrued_yield`, `maturity.total_balance`, `maturity.currency`, `maturity.rollover_url`, and `maturity.withdraw_url`.
- Feature updates: an approved `updates` list containing `title`, `summary`, and optional `url`.
- Security: `security.action_name`, `security.action_summary`, and `security.action_url`.

The current email service supplies `brand_name`, `support_email`, and `site_url` by default, so the campaign adapter should either map those names into the template context or standardize the templates before activation. Account-level email consent, verified addresses, unsubscribe status, bounce suppression, and deduplication must be enforced by the campaign query.

Do not populate the feature-update template with unverified claims about audits, DEX listings, yields, withdrawals, or compliance. Do not send maturity figures unless they are read from the authoritative investment records.
