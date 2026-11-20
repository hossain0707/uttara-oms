"""Verify signatures/claims with synthetic RSA keys, never a live identity provider."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
import uuid
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from app.auth import jwt_claims, current_actor
from app.config import settings


@pytest.fixture
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def claims():
    now = datetime.now(timezone.utc)
    return {"sub":str(uuid.uuid4()), "iss":settings().supabase_issuer,
            "aud":"authenticated", "role":"authenticated", "iat":now,
            "exp":now+timedelta(minutes=5)}


def test_valid_asymmetric_token(signing_key):
    token = jwt.encode(claims(), signing_key, algorithm="RS256")
    with patch("app.auth.jwks_client") as client:
        client.return_value.get_signing_key_from_jwt.return_value.key = signing_key.public_key()
        assert jwt_claims(token)["role"] == "authenticated"


@pytest.mark.parametrize("mutation", ["expired", "issuer", "audience", "role", "missing_exp", "signature", "future_iat"])
def test_invalid_tokens(signing_key, mutation):
    body = claims()
    if mutation == "expired": body["exp"] = datetime.now(timezone.utc)-timedelta(minutes=2)
    if mutation == "issuer": body["iss"] = "https://attacker.invalid"
    if mutation == "audience": body["aud"] = "other"
    if mutation == "role": body["role"] = "service_role"
    if mutation == "missing_exp": del body["exp"]
    if mutation == "future_iat": body["iat"] = datetime.now(timezone.utc)+timedelta(hours=1)
    token = jwt.encode(body, signing_key, algorithm="RS256")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048) if mutation == "signature" else signing_key
    with patch("app.auth.jwks_client") as client:
        client.return_value.get_signing_key_from_jwt.return_value.key = key.public_key()
        with pytest.raises(HTTPException) as error:
            jwt_claims(token)
        assert error.value.status_code == 401


@pytest.mark.parametrize("token", ["malformed", jwt.encode({"sub":"test"}, "test-key-at-least-thirty-two-bytes-long", algorithm="HS256"), jwt.encode({"sub":"test"}, key="", algorithm="none")])
def test_unsupported_tokens_do_not_fetch_keys(token):
    with patch("app.auth.jwks_client") as client:
        with pytest.raises(HTTPException): jwt_claims(token)
        client.assert_not_called()


def test_admin_mfa_and_unapproved_identity():
    from unittest.mock import MagicMock
    db = MagicMock()
    credentials = SimpleNamespace(credentials="synthetic")
    with patch("app.auth.jwt_claims", return_value={"sub":"synthetic", "aal":"aal1"}):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as error: current_actor(credentials, db)
        assert error.value.status_code == 403
        db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(id=uuid.uuid4(), email="test@example.invalid")
        db.query.return_value.filter.return_value.all.return_value = [SimpleNamespace(role="THANA_ADMIN", scope_node_id=None)]
        with pytest.raises(HTTPException, match="Administrator MFA required"):
            current_actor(credentials, db)
