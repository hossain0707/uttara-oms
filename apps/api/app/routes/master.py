"""Owner-controlled policy requests, independent approvals and immediate revocation."""
from datetime import datetime, timezone
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..auth import Actor, current_actor
from ..database import get_db
from ..models import AppUser, RoleGrant, AuditLog, OrgNode
from ..schemas import InputModel
from ..policies import is_thana_admin, lock_organization
from .. import security_policy as policy

router = APIRouter(prefix="/master", tags=["master security"])


def require_reviewer(actor):
    if not is_thana_admin(actor) or not actor.mfa:
        raise HTTPException(403, "An authenticator-verified Thana Admin is required")


def require_owner(db, actor):
    require_reviewer(actor)
    if not policy.is_owner(db, actor.id):
        raise HTTPException(403, "Master Admin/Owner required")


def lock_account(db, user_id):
    user = db.query(AppUser).filter(AppUser.id == user_id).with_for_update().one_or_none()
    if not user:
        raise HTTPException(404, "Account not found")
    return user


class ExceptionRequest(InputModel):
    user_id: UUID
    expected_policy_id: UUID | None = None
    until: datetime | None = None
    reason: str = Field(min_length=5, max_length=50)

    @field_validator("reason")
    @classmethod
    def printable_reason(cls, value):
        if not value.isprintable() or len(value.strip()) < 5:
            raise ValueError("Use a short reason (5-50 characters)")
        return value.strip()

    @field_validator("until")
    @classmethod
    def future(cls, value):
        if value is not None and (value.tzinfo is None or value <= datetime.now(timezone.utc)):
            raise ValueError("Choose a future expiry with a time zone")
        return value


class Decision(InputModel):
    approve: bool


class Revoke(InputModel):
    expected_policy_id: UUID


class AccountStatus(InputModel):
    expected_active: bool
    active: bool


def snapshot(row):
    value = policy.decode(row)
    return {"id": str(row.id) if row else None, "exempt": policy.effective_exception(row),
            "until": value.get("until"), "reason": value.get("reason", ""),
            "expired": bool(value.get("exempt") and value.get("until") and not policy.effective_exception(row))}


@router.get("/security")
def security(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_reviewer(actor)
    owner_uuid = policy.owner_id(db)
    owner = str(actor.id) == owner_uuid
    requests = db.query(AuditLog).filter(AuditLog.action == policy.REQUEST_EVENT).order_by(AuditLog.created_at.desc()).limit(200).all()
    decisions = {r.target_id for r in db.query(AuditLog).filter(AuditLog.action.in_([policy.APPROVE_EVENT, policy.REJECT_EVENT])).all()}
    target_ids = [UUID(r.target_id) for r in requests]
    targets = {str(u.id): u for u in db.query(AppUser).filter(AppUser.id.in_(target_ids)).all()}
    pending = []
    for request in requests:
        if str(request.id) in decisions:
            continue
        target = targets.get(request.target_id)
        value = policy.decode(request)
        pending.append({"id": str(request.id), "user_id": request.target_id,
                        "email": target.email if target else "Unavailable account", "requested_by": str(request.actor_id), **value})
    users = db.query(AppUser).order_by(AppUser.email).limit(500).all() if owner else []
    grants = db.query(RoleGrant).all() if owner else []
    nodes = {n.id: n.name for n in db.query(OrgNode).all()} if owner else {}
    ranked = db.query(AuditLog.id.label("id"), func.row_number().over(partition_by=AuditLog.target_id, order_by=(AuditLog.created_at.desc(), AuditLog.id.desc())).label("rank")).filter(AuditLog.action == policy.POLICY_EVENT).subquery()
    policies = {r.target_id: r for r in db.query(AuditLog).join(ranked, AuditLog.id == ranked.c.id).filter(ranked.c.rank == 1).all()} if owner else {}
    history = db.query(AuditLog).filter(AuditLog.action.in_([policy.POLICY_EVENT, policy.APPROVE_EVENT, policy.REJECT_EVENT, "MASTER_ACCOUNT_STATUS"])).order_by(AuditLog.created_at.desc()).limit(50).all() if owner else []
    return {"is_owner": owner, "default": "Required for administrative accounts", "items": [
        {"id": str(u.id), "email": u.email, "active": u.active, "is_owner": str(u.id) == owner_uuid,
         "roles": [{"role": g.role, "scope_node_id": str(g.scope_node_id) if g.scope_node_id else None, "scope_name": nodes.get(g.scope_node_id)} for g in grants if g.user_id == u.id],
         "policy": snapshot(policies.get(str(u.id)))} for u in users], "pending": pending,
        "history": [{"id": str(h.id), "action": h.action, "actor_id": str(h.actor_id), "target_id": h.target_id, "at": h.created_at.isoformat()} for h in history]}


@router.post("/exceptions", status_code=201)
def request_exception(body: ExceptionRequest, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    lock_organization(db)
    user = lock_account(db, body.user_id)
    if policy.is_owner(db, user.id):
        raise HTTPException(403, "The Master Admin must keep authenticator protection")
    if not user.active or not db.query(RoleGrant).filter(RoleGrant.user_id == user.id).first():
        raise HTTPException(422, "Choose an active account with an administrative role")
    previous = policy.latest_policy(db, user.id)
    if (str(previous.id) if previous else None) != (str(body.expected_policy_id) if body.expected_policy_id else None):
        raise HTTPException(409, "Security policy changed; refresh first")
    requests = db.query(AuditLog).filter(AuditLog.action == policy.REQUEST_EVENT, AuditLog.target_id == str(user.id)).all()
    if any(not policy.resolved(db, r.id) for r in requests):
        raise HTTPException(409, "This account already has a pending security request")
    row = policy.event(db, actor, policy.REQUEST_EVENT, user.id,
                       {"until": body.until.isoformat() if body.until else None, "reason": body.reason, "previous": str(previous.id) if previous else None})
    db.commit()
    return {"id": str(row.id), "status": "PENDING"}


@router.post("/exceptions/{request_id}/decision")
def decide(request_id: UUID, body: Decision, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_reviewer(actor)
    lock_organization(db)
    request = db.query(AuditLog).filter(AuditLog.id == request_id, AuditLog.action == policy.REQUEST_EVENT).with_for_update().one_or_none()
    if not request:
        raise HTTPException(404, "Security request not found")
    if policy.resolved(db, request.id):
        raise HTTPException(409, "Request already reviewed")
    if body.approve and (actor.id == request.actor_id or str(actor.id) == request.target_id):
        raise HTTPException(403, "A different Thana Admin must approve; the target cannot approve their own exception")
    user = lock_account(db, UUID(request.target_id))
    if body.approve:
        if policy.is_owner(db, user.id) or not user.active or not db.query(RoleGrant).filter(RoleGrant.user_id == user.id).first():
            raise HTTPException(409, "Target is no longer eligible")
        # Requests stop being valid if owner authority was transferred outside the app.
        if str(request.actor_id) != policy.owner_id(db):
            raise HTTPException(409, "Requesting owner changed; reject this request")
        value = policy.decode(request)
        previous = policy.latest_policy(db, user.id)
        if value.get("previous") != (str(previous.id) if previous else None):
            raise HTTPException(409, "Security policy changed; reject and request again")
        until = value.get("until")
        if until and datetime.fromisoformat(until) <= datetime.now(timezone.utc):
            raise HTTPException(409, "Requested exception already expired")
        policy.event(db, actor, policy.POLICY_EVENT, user.id, {"exempt": True, "until": until, "reason": value["reason"], "request": str(request.id)})
    policy.event(db, actor, policy.APPROVE_EVENT if body.approve else policy.REJECT_EVENT, request.id, {"user_id": str(user.id)})
    db.commit()
    return {"status": "APPROVED" if body.approve else "REJECTED"}


@router.post("/exceptions/{user_id}/revoke")
def revoke(user_id: UUID, body: Revoke, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    lock_organization(db)
    lock_account(db, user_id)
    previous = policy.latest_policy(db, user_id)
    if not previous or previous.id != body.expected_policy_id:
        raise HTTPException(409, "Security policy changed; refresh first")
    policy.event(db, actor, policy.POLICY_EVENT, user_id, {"exempt": False, "reason": "Revoked by Master Admin"})
    db.commit()
    return {"status": "REQUIRED"}


@router.post("/accounts/{user_id}/status")
def account_status(user_id: UUID, body: AccountStatus, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    lock_organization(db)
    user = lock_account(db, user_id)
    if policy.is_owner(db, user.id):
        raise HTTPException(403, "The Master Admin account cannot be suspended here")
    if user.active != body.expected_active:
        raise HTTPException(409, "Account status changed; refresh first")
    if user.active and not body.active and db.query(RoleGrant).filter(RoleGrant.user_id == user.id, RoleGrant.role == "THANA_ADMIN").first():
        remaining = db.query(RoleGrant.user_id).join(AppUser, AppUser.id == RoleGrant.user_id).filter(RoleGrant.role == "THANA_ADMIN", AppUser.active.is_(True)).distinct().count()
        if remaining <= 2:
            raise HTTPException(409, "Keep two active administrators for independent approvals")
    user.active = body.active
    policy.event(db, actor, "MASTER_ACCOUNT_STATUS", user.id, {"active": user.active})
    db.commit()
    return {"active": user.active}
