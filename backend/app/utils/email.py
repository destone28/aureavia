"""Email utility for sending transactional emails.

Supports multiple email types:
- 2FA verification codes
- Password reset codes
- Ride assignment notifications (forced by admin)

When DEV_MODE=True, emails are logged to console instead of sent via SMTP.
When DEV_MODE=False, emails are sent via SMTP (aiosmtplib).
"""

import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base HTML template
# ---------------------------------------------------------------------------

def _base_template(content_block: str) -> str:
    """Wrap content in the AureaVia branded email template."""
    return f"""\
<!DOCTYPE html>
<html lang="it">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F5F5F5;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F5F5;padding:32px 0;">
  <tr><td align="center">
    <table width="480" cellpadding="0" cellspacing="0" style="font-family:'Open Sans',Arial,sans-serif;">
      <!-- Logo -->
      <tr><td align="center" style="padding-bottom:24px;">
        <h1 style="color:#FF8C00;font-size:28px;margin:0;font-weight:700;">AureaVia</h1>
        <p style="color:#999;font-size:12px;margin:4px 0 0;">Piattaforma di gestione trasporti NCC</p>
      </td></tr>
      <!-- Content card -->
      <tr><td style="background:#fff;border:1px solid #e0e0e0;border-radius:12px;padding:32px;">
        {content_block}
      </td></tr>
      <!-- Footer -->
      <tr><td align="center" style="padding-top:24px;">
        <p style="color:#999;font-size:11px;margin:0;">
          Questa email è stata inviata automaticamente da AureaVia.<br>
          Non rispondere a questo messaggio.
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

def _2fa_template(code: str) -> tuple[str, str]:
    """Return (subject, html) for 2FA verification email."""
    subject = "AureaVia - Codice di verifica"
    content = f"""\
<h2 style="color:#2D2D2D;font-size:20px;margin:0 0 16px;text-align:center;">
  Codice di verifica
</h2>
<p style="color:#666;font-size:14px;margin:0 0 24px;text-align:center;">
  Inserisci il seguente codice per completare l'accesso:
</p>
<div style="background:#F5F5F5;border-radius:8px;padding:16px;margin:0 0 24px;text-align:center;">
  <span style="font-size:32px;font-weight:700;letter-spacing:8px;color:#2D2D2D;">
    {code}
  </span>
</div>
<p style="color:#999;font-size:12px;margin:0;text-align:center;">
  Il codice scade tra 10 minuti.<br>
  Se non hai richiesto l'accesso, ignora questa email.
</p>"""
    return subject, _base_template(content)


def _reset_password_template(code: str) -> tuple[str, str]:
    """Return (subject, html) for password reset email."""
    subject = "AureaVia - Reimpostazione password"
    content = f"""\
<h2 style="color:#2D2D2D;font-size:20px;margin:0 0 16px;text-align:center;">
  Reimpostazione password
</h2>
<p style="color:#666;font-size:14px;margin:0 0 24px;text-align:center;">
  Hai richiesto la reimpostazione della password.<br>
  Usa il seguente codice per completare la procedura:
</p>
<div style="background:#F5F5F5;border-radius:8px;padding:16px;margin:0 0 24px;text-align:center;">
  <span style="font-size:32px;font-weight:700;letter-spacing:8px;color:#2D2D2D;">
    {code}
  </span>
</div>
<p style="color:#999;font-size:12px;margin:0;text-align:center;">
  Il codice scade tra 30 minuti.<br>
  Se non hai richiesto il reset, ignora questa email.
</p>"""
    return subject, _base_template(content)


def _ride_assignment_template(
    driver_name: str,
    ride_date: str,
    pickup: str,
    dropoff: str,
    passenger: str,
) -> tuple[str, str]:
    """Return (subject, html) for forced ride assignment notification."""
    subject = "AureaVia - Nuova corsa assegnata"
    content = f"""\
<h2 style="color:#2D2D2D;font-size:20px;margin:0 0 16px;text-align:center;">
  Corsa assegnata
</h2>
<p style="color:#666;font-size:14px;margin:0 0 24px;text-align:center;">
  Ciao <strong>{driver_name}</strong>, ti è stata assegnata una nuova corsa.
</p>
<table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
  <tr>
    <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
      <span style="color:#999;font-size:12px;">DATA E ORA</span><br>
      <span style="color:#2D2D2D;font-size:14px;font-weight:600;">{ride_date}</span>
    </td>
  </tr>
  <tr>
    <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
      <span style="color:#999;font-size:12px;">PICKUP</span><br>
      <span style="color:#2D2D2D;font-size:14px;">{pickup}</span>
    </td>
  </tr>
  <tr>
    <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
      <span style="color:#999;font-size:12px;">DESTINAZIONE</span><br>
      <span style="color:#2D2D2D;font-size:14px;">{dropoff}</span>
    </td>
  </tr>
  <tr>
    <td style="padding:8px 0;">
      <span style="color:#999;font-size:12px;">PASSEGGERO</span><br>
      <span style="color:#2D2D2D;font-size:14px;">{passenger}</span>
    </td>
  </tr>
</table>
<p style="color:#666;font-size:13px;margin:0;text-align:center;">
  Accedi all'app per visualizzare i dettagli completi della corsa.
</p>"""
    return subject, _base_template(content)


# ---------------------------------------------------------------------------
# Send function (core)
# ---------------------------------------------------------------------------

async def _send_email(to: str, subject: str, html_body: str, plain_text: str) -> bool:
    """Send an email via SMTP.

    Returns True if sent, False on error.
    Logs all errors but never raises — the caller decides how to handle failures.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AureaVia <{settings.EMAIL_FROM}>"
    msg["To"] = to
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("Email sent to %s (subject: %s)", to, subject)
        return True
    except aiosmtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed for %s — check SMTP_USER/SMTP_PASSWORD", settings.SMTP_USER)
        return False
    except aiosmtplib.SMTPConnectError:
        logger.error("Cannot connect to SMTP server %s:%s", settings.SMTP_HOST, settings.SMTP_PORT)
        return False
    except aiosmtplib.SMTPResponseException as e:
        logger.error("SMTP error sending to %s: %s %s", to, e.code, e.message)
        return False
    except Exception:
        logger.exception("Unexpected error sending email to %s", to)
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def send_2fa_email(to: str, code: str) -> bool:
    """Send 2FA verification code.

    In DEV_MODE, logs to console and returns True.
    In production, sends via SMTP.
    """
    if settings.DEV_MODE:
        logger.info("DEV_MODE: 2FA code for %s: %s", to, code)
        print(f"\n  🔐 2FA CODE for {to}: {code}\n")
        return True

    subject, html = _2fa_template(code)
    plain = f"Il tuo codice di verifica AureaVia: {code}\nIl codice scade tra 10 minuti."
    return await _send_email(to, subject, html, plain)


async def send_reset_password_email(to: str, code: str) -> bool:
    """Send password reset code.

    In DEV_MODE, logs to console and returns True.
    In production, sends via SMTP.
    """
    if settings.DEV_MODE:
        logger.info("DEV_MODE: Reset code for %s: %s", to, code)
        print(f"\n  🔑 RESET CODE for {to}: {code}\n")
        return True

    subject, html = _reset_password_template(code)
    plain = f"Codice di reset password AureaVia: {code}\nIl codice scade tra 30 minuti."
    return await _send_email(to, subject, html, plain)


async def send_ride_assignment_email(
    to: str,
    driver_name: str,
    ride_date: str,
    pickup: str,
    dropoff: str,
    passenger: str,
) -> bool:
    """Send ride assignment notification to driver.

    In DEV_MODE, logs to console and returns True.
    In production, sends via SMTP.
    """
    if settings.DEV_MODE:
        logger.info(
            "DEV_MODE: Ride assignment email to %s — %s → %s at %s",
            to, pickup, dropoff, ride_date,
        )
        print(f"\n  📧 RIDE ASSIGNED to {driver_name} ({to}): {pickup} → {dropoff} at {ride_date}\n")
        return True

    subject, html = _ride_assignment_template(driver_name, ride_date, pickup, dropoff, passenger)
    plain = (
        f"Ciao {driver_name}, ti è stata assegnata una nuova corsa.\n"
        f"Data: {ride_date}\nPickup: {pickup}\nDestinazione: {dropoff}\n"
        f"Passeggero: {passenger}\n\nAccedi all'app per i dettagli."
    )
    return await _send_email(to, subject, html, plain)
