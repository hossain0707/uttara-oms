import hashlib
import hmac
import re
from cryptography.fernet import Fernet
from .config import settings


def _cipher():
    return Fernet(settings().encryption_key.encode())


def encrypt(value: str | None) -> str | None:
    return _cipher().encrypt(value.encode()).decode() if value else None


def decrypt(value: str | None) -> str | None:
    return _cipher().decrypt(value.encode()).decode() if value else None


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    n = re.sub(r"[\s()\-]", "", value)
    if n.startswith("+880"):
        n = "0" + n[4:]
    elif n.startswith("880"):
        n = "0" + n[3:]
    if not re.fullmatch(r"01[3-9][0-9]{8}", n):
        raise ValueError("Use a valid Bangladeshi mobile number")
    return n


def phone_digest(value: str | None) -> str | None:
    if not value:
        return None
    return hmac.new(settings().phone_hash_key.encode(), value.encode(), hashlib.sha256).hexdigest()
