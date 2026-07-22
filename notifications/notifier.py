"""Notifier module providing high-level notify helper for AI-OS."""

from .telegram import TelegramNotifier

# Map levels to corresponding emojis
LEVEL_EMOJIS = {
    "info": "ℹ️",
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
}


def notify(message: str, level: str = "info") -> bool:
    """Send a notification message via Telegram with emoji based on level.

    Args:
        message: The text message to send.
        level: Notification level ('info', 'success', 'warning', 'error'). Defaults to 'info'.

    Returns:
        bool: True if the notification was sent successfully, False otherwise.
    """
    emoji = LEVEL_EMOJIS.get(level.lower(), "ℹ️")
    formatted_message = f"{emoji} {message}"
    notifier = TelegramNotifier()
    return notifier.send_message_sync(formatted_message)
