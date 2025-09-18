import smtplib
import ssl
from email.message import EmailMessage
from typing import List, Optional, Sequence
from .config import Config

# PUBLIC_INTERFACE
def send_email(subject: str, body: str, to_addrs: Sequence[str], *, html: bool = False, cc: Optional[Sequence[str]] = None, bcc: Optional[Sequence[str]] = None) -> bool:
    """Send an email using SMTP configuration from environment variables.

    Args:
        subject: Email subject line
        body: Email body (plain text by default; set html=True to send as HTML)
        to_addrs: List/sequence of recipient email addresses
        html: When True, sets Content-Type text/html; otherwise text/plain
        cc: Optional list of CC recipients
        bcc: Optional list of BCC recipients

    Returns:
        True if sending did not raise an exception; False otherwise.

    Notes:
        - Requires SMTP_HOST and NOTIFY_EMAIL_FROM to be set. If missing, function
          returns False and does nothing.
        - Uses SMTP_USE_SSL or SMTP_USE_TLS (default TLS on port 587) for security.
    """
    cfg = Config()
    if not cfg.email_enabled():
        # Not configured; treat as no-op success to avoid failing app flows.
        return False

    from_addr = cfg.notify_email_from
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    if cc:
        msg["Cc"] = ", ".join(cc)

    if html:
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    all_recipients: List[str] = list(to_addrs)
    if cc:
        all_recipients.extend(cc)
    if bcc:
        all_recipients.extend(bcc)

    try:
        if cfg.smtp_use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host=cfg.smtp_host, port=cfg.smtp_port, context=context) as server:
                if cfg.smtp_user:
                    server.login(cfg.smtp_user, cfg.smtp_password)
                server.send_message(msg, from_addr=from_addr, to_addrs=all_recipients)
        else:
            with smtplib.SMTP(host=cfg.smtp_host, port=cfg.smtp_port, timeout=10) as server:
                server.ehlo()
                if cfg.smtp_use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                if cfg.smtp_user:
                    server.login(cfg.smtp_user, cfg.smtp_password)
                server.send_message(msg, from_addr=from_addr, to_addrs=all_recipients)
        return True
    except Exception:
        # Intentionally swallow exceptions to avoid breaking API flows;
        # In production, consider logging with a logger here.
        return False


# PUBLIC_INTERFACE
def get_default_notification_recipients() -> List[str]:
    """Return default recipient list for notifications based on NOTIFY_EMAIL_TO."""
    cfg = Config()
    if not cfg.notify_email_to:
        return []
    return [e.strip() for e in cfg.notify_email_to.split(",") if e.strip()]
