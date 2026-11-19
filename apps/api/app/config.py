from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    supabase_issuer: str
    supabase_jwks_url: str
    jwt_audience: str = "authenticated"
    encryption_key: str
    phone_hash_key: str = Field(min_length=32)
    cors_origins: str = "http://localhost:3000"
    require_admin_mfa: bool = True
    environment: str = "production"

    @field_validator("supabase_issuer", "supabase_jwks_url")
    @classmethod
    def must_be_https(cls, value: str):
        if not value.startswith("https://"):
            raise ValueError("Supabase issuer/JWKS URLs must use HTTPS")
        return value.rstrip("/")

    @property
    def allowed_origins(self):
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]


@lru_cache
def settings() -> Settings:
    return Settings()
