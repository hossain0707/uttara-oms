"""Append-only security policy state. Mutations serialize on the organization root."""
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import AuditLog, AppUser

OWNER_EVENT = "MASTER_OWNER_CONFIGURED"
POLICY_EVENT = "MASTER_MFA_POLICY"
REQUEST_EVENT = "MASTER_MFA_REQUEST"
APPROVE_EVENT = "MASTER_MFA_APPROVED"
REJECT_EVENT = "MASTER_MFA_REJECTED"


def owner_id(db: Session):
    row = db.query(AuditLog).filter(AuditLog.action == OWNER_EVENT).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).first()
    return row.target_id if row else None


def is_owner(db: Session, user_id):
    return str(user_id) == owner_id(db)


def decode(row):
    try:
        value = json.loads(row.detail) if row else {}
        return value if isinstance(value, dict) else {}
    except (ValueError, TypeError):
        return {}


def latest_policy(db: Session, user_id):
    return db.query(AuditLog).filter(AuditLog.action == POLICY_EVENT, AuditLog.target_id == str(user_id)).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).first()


def effective_exception(row):
    value = decode(row)
    if value.get("exempt") is not True:
        return False
    expiry = value.get("until")
    if expiry is None:
        return True
    try:
        instant = datetime.fromisoformat(expiry)
        return instant.tzinfo is not None and instant > datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False


def mfa_exempt(db: Session, user_id):
    return owner_id(db) is not None and not is_owner(db, user_id) and effective_exception(latest_policy(db, user_id))


def event(db, actor, action, target, value):
    detail = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    if len(detail) > 250:
        raise ValueError("Security policy detail exceeds the audit storage limit")
    row = AuditLog(actor_id=actor.id, action=action, target_id=str(target), detail=detail)
    db.add(row)
    db.flush()
    return row


def resolved(db, request_id):
    return db.query(AuditLog).filter(AuditLog.target_id == str(request_id), AuditLog.action.in_([APPROVE_EVENT, REJECT_EVENT])).first()
