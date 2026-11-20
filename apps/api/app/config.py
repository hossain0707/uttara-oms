from functools import lru_cache
from pydantic import Field, field_validator, model_validator
from cryptography.fernet import Fernet
from urllib.parse import urlparse
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

    @field_validator("encryption_key")
    @classmethod
    def valid_encryption_key(cls, value: str):
        Fernet(value.encode())
        return value

    @model_validator(mode="after")
    def production_safety(self):
        origins = self.allowed_origins
        if not origins or any(origin == "*" or urlparse(origin).scheme not in {"https", "http"} or
                              not urlparse(origin).netloc or urlparse(origin).path not in {"", "/"}
                              for origin in origins):
            raise ValueError("CORS requires explicit HTTP(S) origins")
        if self.environment == "production":
            if not self.database_url.startswith("postgresql") or not self.require_admin_mfa:
                raise ValueError("Production requires PostgreSQL and administrator MFA")
            if any(not origin.startswith("https://") for origin in origins):
                raise ValueError("Production CORS origins must use HTTPS")
        return self

    @property
    def allowed_origins(self):
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]


@lru_cache
def settings() -> Settings:
    return Settings()
