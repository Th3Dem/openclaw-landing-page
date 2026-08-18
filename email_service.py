"""Email notification service for OpenClaw AI Dev Team landing page.

Dispatches structured HTML and plaintext email notifications to project stakeholders
when customer lead intake forms are submitted.
"""

import html
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

logger = logging.getLogger("openclaw.email_service")


def load_env_file(filepath: str = ".env") -> None:
    """Parse and load environment variables from a local .env file if it exists."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        logger.warning("Could not parse .env file %s: %s", filepath, e)


# Attempt loading .env upon module initialization
load_env_file()


def get_email_config() -> Dict[str, Any]:
    """Retrieve email and SMTP configuration from environment variables."""
    load_env_file()
    host = os.getenv("SMTP_HOST", "smtp.mail.ru")
    port_str = os.getenv("SMTP_PORT", "465")
    try:
        port = int(port_str)
    except ValueError:
        port = 465
    user = os.getenv("SMTP_USER", "asxdem@mail.ru")
    password = os.getenv("SMTP_PASSWORD", "")
    use_ssl_str = os.getenv("SMTP_USE_SSL", "true").strip().lower()
    use_ssl = use_ssl_str in ("true", "1", "yes") or port == 465
    recipient = os.getenv("NOTIFICATION_RECIPIENT_EMAIL", "asxdem@mail.ru")
    sender = os.getenv("NOTIFICATION_SENDER_EMAIL", user or "asxdem@mail.ru")

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "use_ssl": use_ssl,
        "recipient": recipient,
        "sender": sender,
        "enabled": bool(password.strip()),
    }


def sanitize_header(value: str) -> str:
    """Sanitize header value against CRLF injection."""
    return value.replace("\r", "").replace("\n", "").strip()


def build_email_content(lead_data: Dict[str, Any]) -> tuple[str, str]:
    """Generate plain text and cyber glassmorphism HTML email body for lead notification."""
    lead_id = lead_data.get("lead_id", "N/A")
    name = lead_data.get("name", "Unknown")
    contact = lead_data.get("contact", "Not provided")
    message = lead_data.get("message") or "No additional notes provided."
    client_ip = lead_data.get("client_ip", "Unknown")
    created_at = lead_data.get("created_at", "N/A")

    # Plaintext version
    text_content = f"""=====================================================
🚀 НОВАЯ ЗАЯВКА: OPENCLAW AI DEV TEAM
=====================================================

ID Заявки:      {lead_id}
Имя клиента:    {name}
Контакт:        {contact}
Время (UTC):    {created_at}
IP клиента:     {client_ip}

-----------------------------------------------------
ОПИСАНИЕ ПРОЕКТА / ЗАДАЧИ:
{message}
-----------------------------------------------------
OpenClaw Autonomous AI Dev Team
Landing Page Lead Intake Service
=====================================================
"""

    safe_lead_id = html.escape(str(lead_id))
    safe_name = html.escape(str(name))
    safe_contact = html.escape(str(contact))
    safe_message = html.escape(str(message)).replace("\n", "<br>")
    safe_created_at = html.escape(str(created_at))
    safe_client_ip = html.escape(str(client_ip))

    # Determine contact link
    contact_link = safe_contact
    if "@" in contact and not contact.startswith("@"):
        contact_link = f'<a href="mailto:{safe_contact}" style="color: #10b981; text-decoration: underline;">{safe_contact}</a>'
    elif contact.startswith("@") or ("t.me" in contact):
        handle = contact.replace("https://t.me/", "").replace("@", "")
        contact_link = f'<a href="https://t.me/{html.escape(handle)}" style="color: #06b6d4; text-decoration: underline;">@{html.escape(handle)} (Telegram)</a>'

    # Studio-grade Cyber Dark Theme HTML email
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Новая заявка с лендинга</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f1f5f9;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0b0f19; padding: 40px 10px;">
        <tr>
            <td align="center">
                <table width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%; background-color: #0f172a; border: 1px solid #1e293b; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.15)); padding: 32px 36px; border-bottom: 1px solid #1e293b; text-align: left;">
                            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td>
                                        <span style="display: inline-block; padding: 4px 12px; background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; border-radius: 20px; font-size: 12px; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1px;">⚡ НОВАЯ ЗАЯВКА</span>
                                        <h1 style="margin: 12px 0 4px 0; font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">OpenClaw AI Dev Team</h1>
                                        <p style="margin: 0; font-size: 14px; color: #94a3b8;">Поступила новая клиентская заявка с лендинга</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Main Body -->
                    <tr>
                        <td style="padding: 36px;">
                            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom: 24px;">
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #1e293b; color: #94a3b8; font-size: 13px; font-weight: 600; width: 140px;">ID Заявки:</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #1e293b; color: #38bdf8; font-size: 14px; font-family: monospace; font-weight: 700;">{safe_lead_id}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #1e293b; color: #94a3b8; font-size: 13px; font-weight: 600;">Имя клиента:</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #1e293b; color: #f8fafc; font-size: 16px; font-weight: 700;">{safe_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #1e293b; color: #94a3b8; font-size: 13px; font-weight: 600;">Контакт для связи:</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #1e293b; font-size: 15px; font-weight: 600;">{contact_link}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #1e293b; color: #94a3b8; font-size: 13px; font-weight: 600;">Время (UTC):</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #1e293b; color: #cbd5e1; font-size: 13px;">{safe_created_at}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; color: #94a3b8; font-size: 13px; font-weight: 600;">IP адрес:</td>
                                    <td style="padding: 12px 0; color: #64748b; font-size: 13px; font-family: monospace;">{safe_client_ip}</td>
                                </tr>
                            </table>

                            <!-- Project Scope / Message Box -->
                            <div style="background-color: #0b1120; border: 1px solid #1e293b; border-left: 4px solid #10b981; border-radius: 8px; padding: 18px 20px; margin-top: 10px;">
                                <div style="font-size: 12px; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">Описание задачи / Пожелания:</div>
                                <div style="font-size: 14px; line-height: 1.6; color: #e2e8f0;">{safe_message}</div>
                            </div>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #090d16; padding: 20px 36px; border-top: 1px solid #1e293b; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #64748b;">
                                OpenClaw Autonomous AI Dev Team • Automated Notification Service<br>
                                Сообщение создано и отправлено автоматически при заполнении формы на сайте.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return text_content, html_content


def send_lead_notification_email(lead_data: Dict[str, Any]) -> bool:
    """Dispatch email notification for a newly submitted lead via configured SMTP."""
    config = get_email_config()
    lead_id = lead_data.get("lead_id", "unknown")

    if not config["enabled"]:
        logger.info(
            "[SMTP] Notification email skipped for lead %s: SMTP_PASSWORD is not configured in .env. "
            "Set SMTP_PASSWORD to enable real-time delivery to %s.",
            lead_id,
            config["recipient"],
        )
        return False

    sender = sanitize_header(config["sender"])
    recipient = sanitize_header(config["recipient"])
    subject = sanitize_header(
        f"🚀 Новая заявка с сайта: {lead_data.get('name', 'Клиент')} [{lead_id}]"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"OpenClaw AI Leads <{sender}>"
    msg["To"] = recipient

    text_part, html_part = build_email_content(lead_data)
    msg.attach(MIMEText(text_part, "plain", "utf-8"))
    msg.attach(MIMEText(html_part, "html", "utf-8"))

    try:
        logger.info(
            "[SMTP] Dispatching notification email for lead %s to %s via %s:%s...",
            lead_id,
            recipient,
            config["host"],
            config["port"],
        )
        if config["use_ssl"]:
            with smtplib.SMTP_SSL(config["host"], config["port"], timeout=15) as server:
                server.login(config["user"], config["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(config["host"], config["port"], timeout=15) as server:
                server.starttls()
                server.login(config["user"], config["password"])
                server.send_message(msg)

        logger.info(
            "[SMTP] Notification email successfully sent for lead %s to %s",
            lead_id,
            recipient,
        )
        return True
    except Exception as exc:
        logger.error(
            "[SMTP] Failed to dispatch notification email for lead %s: %s",
            lead_id,
            exc,
            exc_info=True,
        )
        return False
