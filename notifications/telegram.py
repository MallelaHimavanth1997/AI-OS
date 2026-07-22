"""Telegram notification module for AI-OS."""

import logging
import os
import urllib.parse
import urllib.request
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram notification handler for sending automated alerts, updates, and reports."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """Initialize TelegramNotifier with bot token and chat ID.

        If not explicitly provided, attempts to load TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
        from environment variables.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token or not self.chat_id:
            logger.warning(
                "TelegramNotifier: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured. "
                "Notifications will be skipped."
            )

    @property
    def api_url(self) -> str:
        """Construct the base Telegram API URL for sending messages."""
        return f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def is_configured(self) -> bool:
        """Check if TelegramNotifier has valid token and chat ID configured."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram notification skipped: Bot token or Chat ID not set.")
            return False
        return True

    def send_message_sync(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message synchronously using httpx or urllib fallback.

        Args:
            text: Message text to send.
            parse_mode: Formatting mode (HTML, Markdown, etc.). Default is HTML.

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self.is_configured():
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        try:
            if httpx:
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(self.api_url, data=payload)
                    if response.status_code == 200:
                        logger.info("Telegram sync message sent successfully.")
                        return True
                    logger.warning(
                        f"Failed to send Telegram message, status: {response.status_code}, response: {response.text}"
                    )
                    return False
            else:
                data = urllib.parse.urlencode(payload).encode("utf-8")
                req = urllib.request.Request(self.api_url, data=data, method="POST")
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        logger.info("Telegram sync message sent successfully via urllib.")
                        return True
                    logger.warning(f"Failed to send Telegram message, status code: {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"Error sending sync Telegram notification: {e}")
            return False

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message asynchronously using httpx.

        Args:
            text: Message text to send.
            parse_mode: Formatting mode (HTML, Markdown, etc.). Default is HTML.

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self.is_configured():
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        try:
            if httpx:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(self.api_url, data=payload)
                    if response.status_code == 200:
                        logger.info("Telegram async message sent successfully.")
                        return True
                    logger.warning(
                        f"Failed to send async Telegram message, status: {response.status_code}, response: {response.text}"
                    )
                    return False
            else:
                # Fallback to sync urllib execution if httpx is not installed
                return self.send_message_sync(text, parse_mode=parse_mode)
        except Exception as e:
            logger.warning(f"Error sending async Telegram notification: {e}")
            return False

    def send_job_applied(self, job_title: str, company: str, status: str = "Applied") -> bool:
        """Send notification when a job application is processed.

        Args:
            job_title: Position title.
            company: Company name.
            status: Status of the job application (default: "Applied").

        Returns:
            bool: True if message sent successfully, False otherwise.
        """
        message = (
            f"💼 <b>Job Application Alert</b>\n\n"
            f"<b>Position:</b> {job_title}\n"
            f"<b>Company:</b> {company}\n"
            f"<b>Status:</b> {status}"
        )
        return self.send_message_sync(message)

    async def send_job_applied_async(self, job_title: str, company: str, status: str = "Applied") -> bool:
        """Send job application notification asynchronously."""
        message = (
            f"💼 <b>Job Application Alert</b>\n\n"
            f"<b>Position:</b> {job_title}\n"
            f"<b>Company:</b> {company}\n"
            f"<b>Status:</b> {status}"
        )
        return await self.send_message(message)

    def send_report(self, total_applied: int, total_emailed: int, mode: str = "Daily") -> bool:
        """Send summary report notification.

        Args:
            total_applied: Total count of job applications submitted.
            total_emailed: Total count of emails sent.
            mode: Operating mode or report header string.

        Returns:
            bool: True if message sent successfully, False otherwise.
        """
        message = (
            f"📊 <b>AI-OS Execution Report ({mode})</b>\n\n"
            f"<b>Jobs Applied:</b> {total_applied}\n"
            f"<b>Emails Sent:</b> {total_emailed}\n"
            f"<b>Mode:</b> {mode}"
        )
        return self.send_message_sync(message)

    async def send_report_async(self, total_applied: int, total_emailed: int, mode: str = "Daily") -> bool:
        """Send summary report notification asynchronously."""
        message = (
            f"📊 <b>AI-OS Execution Report ({mode})</b>\n\n"
            f"<b>Jobs Applied:</b> {total_applied}\n"
            f"<b>Emails Sent:</b> {total_emailed}\n"
            f"<b>Mode:</b> {mode}"
        )
        return await self.send_message(message)

    def send_error(self, error_msg: str) -> bool:
        """Send error message notification.

        Args:
            error_msg: Error message or traceback summary.

        Returns:
            bool: True if message sent successfully, False otherwise.
        """
        message = (
            f"🚨 <b>AI-OS Error Alert</b>\n\n"
            f"<b>Error:</b> {error_msg}"
        )
        return self.send_message_sync(message)

    async def send_error_async(self, error_msg: str) -> bool:
        """Send error message notification asynchronously."""
        message = (
            f"🚨 <b>AI-OS Error Alert</b>\n\n"
            f"<b>Error:</b> {error_msg}"
        )
        return await self.send_message(message)
