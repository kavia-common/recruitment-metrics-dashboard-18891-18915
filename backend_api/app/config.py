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
    """
    postgres_url: str = os.getenv("POSTGRES_URL", "")
    postgres_user: str = os.getenv("POSTGRES_USER", "")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    postgres_db: str = os.getenv("POSTGRES_DB", "")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    sqlalchemy_echo: bool = os.getenv("SQLALCHEMY_ECHO", "0") == "1"
    env: str = os.getenv("FLASK_ENV", "development")

    # PUBLIC_INTERFACE
    def sqlalchemy_uri(self) -> str:
        """Return the SQLAlchemy database URI constructed from env vars."""
        # Support cases where POSTGRES_URL is already a DSN like postgresql+psycopg://...
        if self.postgres_url.startswith("postgresql"):
            return self.postgres_url

        host = self.postgres_url or "localhost"
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{host}:{self.postgres_port}/{self.postgres_db}"
