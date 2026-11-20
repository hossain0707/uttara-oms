from dataclasses import dataclass
from functools import lru_cache
from uuid import UUID
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import AppUser, RoleGrant

bearer = HTTPBearer(auto_error=True)


@dataclass(frozen=True)
class Actor:
    id: UUID
    email: str
    grants: list[tuple[str, UUID | None]]
    mfa: bool


@lru_cache(maxsize=4)
def jwks_client(url: str):
    return jwt.PyJWKClient(url, cache_jwk_set=True, lifespan=300, timeout=5)


def jwt_claims(token: str) -> dict:
    config = settings()
    try:
        # Only asymmetric signing keys are accepted. HS256 legacy tokens are rejected.
        if jwt.get_unverified_header(token).get("alg") not in {"RS256", "ES256"}:
            raise ValueError("Unsupported signing algorithm")
        key = jwks_client(config.supabase_jwks_url).get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token, key, algorithms=["RS256", "ES256"],
            audience=config.jwt_audience, issuer=config.supabase_issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            leeway=20,
        )
        if claims.get("role") != "authenticated":
            raise ValueError("wrong JWT role")
        return claims
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid access token") from exc


def account_actor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Actor:
    claims = jwt_claims(credentials.credentials)
    user = db.query(AppUser).filter(AppUser.auth_sub == claims["sub"], AppUser.active.is_(True)).first()
    if user is None:
        raise HTTPException(403, "Account has not been approved for OMS")
    grants = db.query(RoleGrant).filter(RoleGrant.user_id == user.id).all()
    mfa = claims.get("aal") == "aal2"
    if settings().require_admin_mfa and not mfa and any(g.role == "THANA_ADMIN" for g in grants):
        raise HTTPException(403, "Administrator MFA required")
    return Actor(user.id, user.email, [(g.role, g.scope_node_id) for g in grants], mfa)


def current_actor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Actor:
    actor = account_actor(credentials, db)
    if not actor.grants:
        raise HTTPException(403, "Organizational role required")
    return actor
