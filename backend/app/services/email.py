import asyncio
import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import getSettings
from core.logging import logger
from services.jira import build_jira_browse_url


def _send_email_sync(
    to_email: str, subject: str, body_html: str, body_text: str
) -> bool:
    settings = getSettings()

    if not all(
        [
            settings.SMTP_SERVER,
            settings.SMTP_PORT,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
        ]
    ):
        logger.warning("SMTP email configurations are missing. Email was not sent.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USERNAME
    msg["To"] = to_email

    # Attach both plain text and HTML versions
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(
            settings.SMTP_SERVER, settings.SMTP_PORT, timeout=10.0
        ) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USERNAME, to_email, msg.as_string())
        logger.info("Successfully sent email to %s with subject: %s", to_email, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s via SMTP: %s", to_email, e)
        return False


async def send_approval_email(
    user_email: str, ticket_key: str, ticket_title: str
) -> bool:
    safe_key = html.escape(ticket_key, quote=True)
    safe_title = html.escape(ticket_title, quote=True)
    ticket_url = build_jira_browse_url(ticket_key)

    subject = f"Your bug report has been approved: {ticket_key}"

    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
          <div style="background-color: #0052CC; padding: 20px; text-align: center; color: #ffffff;">
            <h2 style="margin: 0; font-size: 24px;">Bug Report Approved</h2>
          </div>
          <div style="padding: 20px;">
            <p>Hello,</p>
            <p>Your bug report has been reviewed and approved by an administrator. A Jira ticket has been successfully created to track this issue.</p>

            <div style="background-color: #f4f5f7; border-left: 4px solid #0052CC; padding: 15px; margin: 20px 0; border-radius: 4px;">
              <p style="margin: 0 0 8px 0;"><strong>Jira Key:</strong> <a href="{html.escape(ticket_url, quote=True)}" style="color: #0052CC; text-decoration: none; font-weight: bold;">{safe_key}</a></p>
              <p style="margin: 0;"><strong>Title:</strong> {safe_title}</p>
            </div>

            <p>Our engineering team will begin working on it shortly. You can track progress directly on the ticket page.</p>
            <p>Best regards,<br>The Support Team</p>
          </div>
          <div style="background-color: #f4f5f7; padding: 10px 20px; text-align: center; font-size: 12px; color: #7a869a; border-top: 1px solid #e0e0e0;">
            This is an automated notification. Please do not reply directly to this email.
          </div>
        </div>
      </body>
    </html>
    """

    body_text = (
        f"Hello,\n\n"
        f"Your bug report has been reviewed and approved by an administrator. "
        f"A Jira ticket has been successfully created to track this issue.\n\n"
        f"Jira Key: {ticket_key}\n"
        f"Ticket Link: {ticket_url}\n"
        f"Title: {ticket_title}\n\n"
        f"Our engineering team will begin working on it shortly. "
        f"You can track progress directly on the ticket page.\n\n"
        f"Best regards,\n"
        f"The Support Team"
    )

    return await asyncio.to_thread(
        _send_email_sync, user_email, subject, body_html, body_text
    )


async def send_rejection_email(user_email: str, ticket_title: str) -> bool:
    safe_title = html.escape(ticket_title, quote=True)
    subject = "Update on your bug report"

    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
          <div style="background-color: #DE350B; padding: 20px; text-align: center; color: #ffffff;">
            <h2 style="margin: 0; font-size: 24px;">Bug Report Rejected</h2>
          </div>
          <div style="padding: 20px;">
            <p>Hello,</p>
            <p>Thank you for submitting a bug report. An administrator has reviewed your report and decided not to proceed with creating a Jira ticket for it.</p>

            <div style="background-color: #f4f5f7; border-left: 4px solid #DE350B; padding: 15px; margin: 20px 0; border-radius: 4px;">
              <p style="margin: 0;"><strong>Report Title:</strong> {safe_title}</p>
            </div>

            <p>This decision might be due to the issue already being known, insufficient detail to reproduce, or because the behavior is intended. If you believe this was an error, please start a new chat with the support bot and provide additional details.</p>
            <p>Best regards,<br>The Support Team</p>
          </div>
          <div style="background-color: #f4f5f7; padding: 10px 20px; text-align: center; font-size: 12px; color: #7a869a; border-top: 1px solid #e0e0e0;">
            This is an automated notification. Please do not reply directly to this email.
          </div>
        </div>
      </body>
    </html>
    """

    body_text = (
        f"Hello,\n\n"
        f"Thank you for submitting a bug report. An administrator has reviewed your "
        f"report and decided not to proceed with creating a Jira ticket for it.\n\n"
        f"Report Title: {ticket_title}\n\n"
        f"This decision might be due to the issue already being known, insufficient "
        f"detail to reproduce, or because the behavior is intended. If you believe "
        f"this was an error, please start a new chat with the support bot and "
        f"provide additional details.\n\n"
        f"Best regards,\n"
        f"The Support Team"
    )

    return await asyncio.to_thread(
        _send_email_sync, user_email, subject, body_html, body_text
    )
