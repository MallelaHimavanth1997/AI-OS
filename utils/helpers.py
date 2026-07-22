"""Helper utility functions for AI-OS."""

import re


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncate text to a maximum number of characters.

    Args:
        text (str): The input text to truncate.
        max_chars (int, optional): Maximum allowed length. Defaults to 500.

    Returns:
        str: Truncated text with '...' appended if truncated, or original text.
    """
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3].rstrip() + "..."


def format_job_title(title: str, max_length: int = 100) -> str:
    """Clean and normalize job title text by stripping excess whitespace.

    Args:
        title (str): The job title string.
        max_length (int, optional): Max length for the title. Defaults to 100.

    Returns:
        str: Cleaned and formatted job title.
    """
    if not title:
        return ""
    # Normalize multiple whitespace characters into a single space
    cleaned = re.sub(r"\s+", " ", title).strip()
    return truncate_text(cleaned, max_chars=max_length)


def sanitize_filename(name: str) -> str:
    """Convert a string into a safe filename by removing invalid characters.

    Args:
        name (str): The input string to sanitize.

    Returns:
        str: A sanitized, safe filename string.
    """
    if not name:
        return "unnamed"
    # Replace characters that are invalid in Windows / Posix file names
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
    # Replace whitespace sequences with underscores
    sanitized = re.sub(r"\s+", "_", sanitized)
    # Remove any character that isn't alphanumeric, underscore, hyphen, or dot
    sanitized = re.sub(r"[^\w\.-]", "", sanitized)
    # Remove leading/trailing dots or underscores
    sanitized = sanitized.strip("._")
    return sanitized if sanitized else "unnamed"


def extract_emails_from_text(text: str) -> list[str]:
    """Extract all email addresses from a text string using regex.

    Args:
        text (str): Input text containing potential email addresses.

    Returns:
        list[str]: A list of unique email addresses found in the text.
    """
    if not text:
        return []
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    found = re.findall(pattern, text)
    # Deduplicate while preserving order
    seen = set()
    unique_emails = []
    for email in found:
        lowered = email.lower()
        if lowered not in seen:
            seen.add(lowered)
            unique_emails.append(email)
    return unique_emails


def is_remote_job(title: str, description: str) -> bool:
    """Determine if a job is remote or hybrid based on title and description.

    Args:
        title (str): Job title.
        description (str): Job description.

    Returns:
        bool: True if 'remote' or 'hybrid' is found in title or description.
    """
    combined = f"{title or ''} {description or ''}".lower()
    keywords = ["remote", "hybrid", "work from home", "wfh"]
    return any(keyword in combined for keyword in keywords)
