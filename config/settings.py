"""Settings module for AI-OS configuration management."""

import os
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Path to the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file in the root directory
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Application settings loaded from environment variables and .env file."""

    def __init__(self) -> None:
        # AI & API Credentials
        self.GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
        self.TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")

        # Email Credentials
        self.EMAIL_USER: str | None = os.getenv("EMAIL_USER")
        self.EMAIL_PASSWORD: str | None = os.getenv("EMAIL_PASSWORD")

        # LinkedIn Credentials (optional)
        self.LINKEDIN_EMAIL: str | None = os.getenv("LINKEDIN_EMAIL")
        self.LINKEDIN_PASSWORD: str | None = os.getenv("LINKEDIN_PASSWORD")

        # Job Search Settings
        self.JOB_TITLES: str = os.getenv(
            "JOB_TITLES", "Data Engineer,Cloud Data Engineer"
        )
        self.JOB_LOCATION: str = os.getenv("JOB_LOCATION", "United States")

        raw_remote = os.getenv("JOB_REMOTE_ONLY", "True")
        self.JOB_REMOTE_ONLY: bool = str(raw_remote).strip().lower() in (
            "true",
            "1",
            "yes",
            "t",
        )

        try:
            self.MAX_JOBS_PER_SEARCH: int = int(
                os.getenv("MAX_JOBS_PER_SEARCH", "5")
            )
        except ValueError:
            self.MAX_JOBS_PER_SEARCH = 5

        # Schedule Settings
        self.WORKDAY_START: str = os.getenv("WORKDAY_START", "07:00")
        self.WORKDAY_END: str = os.getenv("WORKDAY_END", "21:00")

        # Environment Settings
        self.APP_ENV: str = os.getenv("APP_ENV", "development")

    def get_job_titles(self) -> list[str]:
        """Return JOB_TITLES as a list of trimmed strings.

        Returns:
            list[str]: List of job titles.
        """
        if not self.JOB_TITLES:
            return []
        return [
            title.strip()
            for title in self.JOB_TITLES.split(",")
            if title.strip()
        ]

    def is_development(self) -> bool:
        """Check if application environment is development.

        Returns:
            bool: True if APP_ENV is development, False otherwise.
        """
        return self.APP_ENV.lower() == "development"

    def validate(self) -> list[str]:
        """Check required keys and print warnings for missing ones.

        Returns:
            list[str]: A list of missing required setting names.
        """
        required_keys = [
            ("GEMINI_API_KEY", self.GEMINI_API_KEY),
            ("TELEGRAM_BOT_TOKEN", self.TELEGRAM_BOT_TOKEN),
            ("TELEGRAM_CHAT_ID", self.TELEGRAM_CHAT_ID),
            ("EMAIL_USER", self.EMAIL_USER),
            ("EMAIL_PASSWORD", self.EMAIL_PASSWORD),
        ]
        missing = []
        for key_name, value in required_keys:
            if not value:
                missing.append(key_name)
                warning_msg = (
                    f"Configuration Warning: Required environment variable "
                    f"'{key_name}' is missing or empty."
                )
                print(f"[WARNING] {warning_msg}")
                warnings.warn(warning_msg, UserWarning, stacklevel=2)
        return missing


# Singleton instance
settings = Settings()
