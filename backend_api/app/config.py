import os
from dataclasses import dataclass

# PUBLIC_INTERFACE
@dataclass
class Config:
    """Application configuration loaded from environment variables.

    Required environment variables:
    - POSTGRES_URL: The hostname or full URL for PostgreSQL (host or DSN style)
    - POSTGRES_USER: Username
    - POSTGRES_PASSWORD: Password
    - POSTGRES_DB: Database name
    - POSTGRES_PORT: Port (e.g., 5432)

    Optional:
    - FLASK_ENV: development/production/test
    - SQLALCHEMY_ECHO: "1" to echo SQL
    - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, NOTIFY_EMAIL_FROM, NOTIFY_EMAIL_TO, SMTP_USE_TLS, SMTP_USE_SSL
    """
    postgres_url: str = os.getenv("POSTGRES_URL", "")
    postgres_user: str = os.getenv("POSTGRES_USER", "")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    postgres_db: str = os.getenv("POSTGRES_DB", "")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    sqlalchemy_echo: bool = os.getenv("SQLALCHEMY_ECHO", "0") == "1"
    env: str = os.getenv("FLASK_ENV", "development")

    # Email/SMTP settings
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587") or "587")
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "1") == "1"
    smtp_use_ssl: bool = os.getenv("SMTP_USE_SSL", "0") == "1"
    notify_email_from: str = os.getenv("NOTIFY_EMAIL_FROM", "")
    # Optional default recipients (comma separated). Services may override.
    notify_email_to: str = os.getenv("NOTIFY_EMAIL_TO", "")

    # PUBLIC_INTERFACE
    def sqlalchemy_uri(self) -> str:
        """Return the SQLAlchemy database URI constructed from env vars."""
        # Support cases where POSTGRES_URL is already a DSN like postgresql+psycopg://...
        if self.postgres_url.startswith("postgresql"):
            return self.postgres_url

        host = self.postgres_url or "localhost"
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{host}:{self.postgres_port}/{self.postgres_db}"

    # PUBLIC_INTERFACE
    def email_enabled(self) -> bool:
        """Return True if SMTP is sufficiently configured to send emails."""
        return bool(self.smtp_host and self.notify_email_from)
