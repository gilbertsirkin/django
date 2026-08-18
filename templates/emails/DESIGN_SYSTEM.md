# WolvCapital Email Design System — "Vault"

Calm, light, trustworthy. Built for a financial platform where the emails
need to feel like a bank statement, not a promotion.

## Tokens

| Token              | Hex       | Use                                          |
|---------------------|-----------|-----------------------------------------------|
| `--bg`              | `#F7F8FA` | Outer email background                        |
| `--card`            | `#FFFFFF` | Card / content surface                        |
| `--ink`             | `#16211D` | Primary text                                  |
| `--ink-soft`        | `#5B6660` | Secondary text, captions                      |
| `--border`          | `#E2E6E3` | Hairlines, table borders                      |
| `--blue`            | `#1B5FA8` | Primary brand accent, headings, links         |
| `--blue-tint`       | `#EAF1FA` | Info box background                           |
| `--coral`           | `#E8734A` | Warnings only — never primary CTA             |
| `--coral-tint`      | `#FDF0EA` | Warning box background                        |
| `--red`             | `#C1443B` | Errors / rejections                           |
| `--red-tint`        | `#FBEDEC` | Error box background                          |

Font stack (email-safe): `Helvetica Neue, Helvetica, Arial, sans-serif`
Numerals/amounts: same stack, letter-spacing 0.2px, weight 600 — no monospace
(monospace read as "crypto ticker," Vault stays calm, not techy).

## Signature element: the Seal

A small circular mark (⬤ with a checkmark or icon) placed next to the
headline on any email confirming a completed/verified action (email
verified, KYC approved, transaction approved, payout sent). Reinforces
trust without icons/emoji scattered through body copy. Rendered as a
36px circle, `--teal` fill, white glyph, using a table cell (not a
background-image) so it survives image-blocking email clients.

## Structural rule

All layout uses nested `<table>` elements (not divs) for Outlook/Windows
Mail compatibility. Every template is either:

- `templates/emails/transactional/base.html` — account, security, money,
  KYC. Sent from `notify@wolvcapital.com` (transactional subdomain/stream).
- `templates/emails/marketing/base.html` — drip campaigns, announcements,
  product news. Sent from `news@wolvcapital.com` (marketing subdomain/stream),
  always includes List-Unsubscribe + visible unsubscribe link + mailing
  address, per CAN-SPAM.

## Copy rules carried over from the audit

- No "guarantee," "guaranteed returns," or unqualified "profit" language.
- Use "projected return," "historical performance," "est. payout" instead.
- One primary CTA per email. No emoji in headings (⚠️ 🔐 removed).
