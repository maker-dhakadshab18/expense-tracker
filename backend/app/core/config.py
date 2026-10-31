from pydantic_settings import BaseSettings, SettingsConfigDict


def _to_psycopg_url(url: str) -> str:
    """Neon/Heroku-style URLs use postgresql:// or postgres://; SQLAlchemy needs the driver named."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str | None = None
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    # Comma-separated list of exact origins, e.g. "http://localhost:3000,https://x.vercel.app"
    cors_origins: str = "http://localhost:3000"
    # Optional regex, e.g. for Vercel preview URLs
    cors_origin_regex: str | None = None

    @property
    def sqlalchemy_url(self) -> str:
        return _to_psycopg_url(self.database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
