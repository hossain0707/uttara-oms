"""Safe local defaults; deployment configuration is never used for test data."""
import os
from cryptography.fernet import Fernet

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite://")
os.environ.setdefault("SUPABASE_ISSUER", "https://example.supabase.co/auth/v1")
os.environ.setdefault("SUPABASE_JWKS_URL", "https://example.supabase.co/auth/v1/.well-known/jwks.json")
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("PHONE_HASH_KEY", "synthetic-test-hmac-key-at-least-32-characters")
os.environ.setdefault("ENVIRONMENT", "test")
