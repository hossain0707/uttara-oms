"""Owner-controlled policy requests, independent approvals and immediate revocation."""
from datetime import datetime, timezone
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..auth import Actor, current_actor
from ..database import get_db
from ..models import AppUser, RoleGrant, AuditLog, OrgNode, AccessRequest, ChangeRequest, Member, PersonalProfile, PersonalReport
from ..schemas import InputModel
from ..policies import is_thana_admin, lock_organization
from .. import security_policy as policy
from ..owner_controls import direct_owner, roles_version, deleted
from .personal import unpack, pack
from .access import active_scope, apply_access_decision
from .directory import name_key, matches
import hashlib
import json

router = APIRouter(prefix="/master", tags=["master security"])


def require_reviewer(actor):
    if not is_thana_admin(actor) or not actor.mfa:
        raise HTTPException(403, "An authenticator-verified Thana Admin is required")


def require_owner(db, actor):
    require_reviewer(actor)
    if not direct_owner(db, actor):
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
    # A direct owner policy supersedes pending requests without modifying immutable events.
    supersede_security(db, actor, user.id)
    row = policy.event(db, actor, policy.POLICY_EVENT, user.id,
                       {"exempt": True, "until": body.until.isoformat() if body.until else None, "reason": body.reason, "direct": True})
    db.commit()
    return {"id": str(row.id), "status": "APPLIED"}


@router.post("/exceptions/{request_id}/decision")
def decide(request_id: UUID, body: Decision, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_reviewer(actor)
    lock_organization(db)
    # Audit events are immutable and the runtime deliberately has no UPDATE privilege.
    # The organization lock above serializes decisions; do not row-lock audit_logs.
    request = db.query(AuditLog).filter(AuditLog.id == request_id, AuditLog.action == policy.REQUEST_EVENT).one_or_none()
    if not request:
        raise HTTPException(404, "Security request not found")
    if policy.resolved(db, request.id):
        raise HTTPException(409, "Request already reviewed")
    if body.approve and (actor.id == request.actor_id or str(actor.id) == request.target_id) and not direct_owner(db, actor):
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
    supersede_security(db, actor, user_id)
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
    if deleted(db, user.id):
        raise HTTPException(409, "Deleted OMS accounts cannot be reactivated")
    user.active = body.active
    policy.event(db, actor, "MASTER_ACCOUNT_STATUS", user.id, {"active": user.active})
    db.commit()
    return {"active": user.active}


def supersede_security(db, actor, user_id):
    requests = db.query(AuditLog).filter(AuditLog.action == policy.REQUEST_EVENT, AuditLog.target_id == str(user_id)).all()
    for request in requests:
        if not policy.resolved(db, request.id):
            policy.event(db, actor, policy.REJECT_EVENT, request.id, {"user_id": str(user_id), "reason": "Superseded by owner action"})


def supersede_access(db, actor, subject, role=None, scope=None):
    query = db.query(AccessRequest).filter(AccessRequest.auth_sub == subject, AccessRequest.status == "PENDING")
    if role is not None:
        query = query.filter(AccessRequest.role == role, AccessRequest.scope_node_id == scope)
    for row in query.all():
        row.status = "REJECTED"
        row.reviewed_by = actor.id
        row.reviewed_at = datetime.now(timezone.utc)
        policy.event(db, actor, "ACCESS_SUPERSEDED", row.id, {"reason": "Direct owner action"})


@router.get("/accounts")
def accounts(q: str = Query(default="", max_length=120), state: Literal["all", "active", "suspended", "deleted"] = "all",
             limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0),
             actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    removed = {r.target_id for r in db.query(AuditLog.target_id).filter(AuditLog.action == "MASTER_ACCOUNT_DELETED").all()}
    all_accounts = db.query(AppUser).order_by(func.lower(AppUser.email), AppUser.id).all()
    terms = name_key(q).split()
    names = {}
    # Stream encrypted rows; retain only names, never photos/documents/report contents.
    wanted = {u.id for u in all_accounts} if q.strip() else {u.id for u in all_accounts[offset:offset + limit]} if state == "all" else {u.id for u in all_accounts}
    for profile in db.query(PersonalProfile).filter(PersonalProfile.user_id.in_(wanted)).yield_per(20):
        names[profile.user_id] = unpack(profile.details_encrypted).get("full_name", "")
    selected = []
    for user in all_accounts:
        erased = str(user.id) in removed
        actual = "deleted" if erased else "active" if user.active else "suspended"
        if state != "all" and state != actual:
            continue
        if q.strip() and q.casefold().strip() not in user.email.casefold() and not (terms and matches(terms, names.get(user.id))):
            continue
        selected.append(user)
    page = selected[offset:offset + limit]
    ids = [u.id for u in page]
    grants = db.query(RoleGrant).filter(RoleGrant.user_id.in_(ids)).all()
    scopes = {n.id: n.name for n in db.query(OrgNode).all()}
    owner_uuid = policy.owner_id(db)
    items = []
    for user in page:
        assigned = [g for g in grants if g.user_id == user.id]
        items.append({"id": str(user.id), "email": user.email, "full_name": names.get(user.id, ""), "active": user.active,
                      "deleted": str(user.id) in removed, "is_owner": str(user.id) == owner_uuid,
                      "roles_version": roles_version(assigned),
                      "roles": [{"id": str(g.id), "role": g.role, "scope_node_id": str(g.scope_node_id) if g.scope_node_id else None,
                                 "scope_name": scopes.get(g.scope_node_id)} for g in assigned],
                      "policy": snapshot(policy.latest_policy(db, user.id))})
    policy.event(db, actor, "MASTER_ACCOUNTS_READ", "accounts", {"offset": offset, "limit": limit, "returned": len(items)})
    db.commit()
    return {"items": items, "total": len(selected), "limit": limit, "offset": offset,
            "stats": {"registered": len(all_accounts), "active": sum(u.active and str(u.id) not in removed for u in all_accounts),
                      "suspended": sum(not u.active and str(u.id) not in removed for u in all_accounts), "deleted": len(removed)}}


class RoleAction(InputModel):
    operation: Literal["GRANT", "REVOKE", "REPLACE"]
    role: Literal["THANA_ADMIN", "THANA_VIEWER", "WARD_ADMIN", "UNIT_EDITOR"]
    scope_node_id: UUID | None = None
    grant_id: UUID | None = None
    expected_roles_version: str = Field(min_length=64, max_length=64)


@router.post("/accounts/{user_id}/roles")
def direct_role(user_id: UUID, body: RoleAction, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    lock_organization(db)
    user = lock_account(db, user_id)
    if deleted(db, user.id):
        raise HTTPException(409, "Deleted OMS accounts cannot receive permissions")
    grants = db.query(RoleGrant).filter(RoleGrant.user_id == user.id).all()
    if roles_version(grants) != body.expected_roles_version:
        raise HTTPException(409, "Permissions changed; refresh before applying")
    if body.role in {"THANA_ADMIN", "THANA_VIEWER"} and body.scope_node_id:
        raise HTTPException(422, "Thana roles must not have a scope")
    if body.operation in {"GRANT", "REPLACE"}:
        if not user.active:
            raise HTTPException(409, "Reactivate this suspended account first")
        if body.role in {"WARD_ADMIN", "UNIT_EDITOR"} and not active_scope(db, db.get(OrgNode, body.scope_node_id) if body.scope_node_id else None, body.role):
            raise HTTPException(422, "Choose an active matching scope")
    old = next((g for g in grants if g.id == body.grant_id), None)
    if body.operation in {"REVOKE", "REPLACE"} and old is None:
        raise HTTPException(409, "Permission no longer assigned; refresh")
    if old and old.role == "THANA_ADMIN" and policy.is_owner(db, user.id):
        raise HTTPException(403, "The Master Admin role is protected")
    def apply(role, scope, operation):
        supersede_access(db, actor, user.auth_sub, role, scope)
        row = AccessRequest(auth_sub=user.auth_sub, email=user.email, role=role, scope_node_id=scope,
                            operation=operation, requested_by=actor.id)
        db.add(row); db.flush()
        apply_access_decision(db, actor, row, True)
    if old and body.operation in {"REVOKE", "REPLACE"}:
        apply(old.role, old.scope_node_id, "REVOKE")
    if body.operation in {"GRANT", "REPLACE"}:
        apply(body.role, body.scope_node_id, "GRANT")
    db.commit()
    return {"status": "APPLIED"}


@router.get("/requests")
def owner_requests(kind: Literal["access", "member", "security"] = "access", limit: int = Query(default=20, ge=1, le=100),
                   offset: int = Query(default=0, ge=0), actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    if kind == "access":
        query = db.query(AccessRequest).filter(AccessRequest.status == "PENDING")
        total = query.count()
        rows = query.order_by(AccessRequest.requested_at, AccessRequest.id).offset(offset).limit(limit).all()
        items = [{"id": str(r.id), "target": r.email, "detail": r.operation + " " + r.role, "kind": kind,
                  "path": "/access/requests/" + str(r.id) + "/decision"} for r in rows]
    elif kind == "member":
        query = db.query(ChangeRequest).filter(ChangeRequest.status == "PENDING")
        total = query.count()
        rows = query.order_by(ChangeRequest.requested_at, ChangeRequest.id).offset(offset).limit(limit).all()
        members = {m.id: m for m in db.query(Member).filter(Member.id.in_([r.member_id for r in rows])).all()}
        items = [{"id": str(r.id), "target": members[r.member_id].full_name, "detail": r.kind + " → " + r.proposed_value,
                  "kind": kind, "path": "/approvals/" + str(r.id) + "/decision"} for r in rows]
    else:
        resolved = {r.target_id for r in db.query(AuditLog.target_id).filter(AuditLog.action.in_([policy.APPROVE_EVENT, policy.REJECT_EVENT])).all()}
        rows = [r for r in db.query(AuditLog).filter(AuditLog.action == policy.REQUEST_EVENT).order_by(AuditLog.created_at, AuditLog.id).yield_per(50) if str(r.id) not in resolved]
        total = len(rows)
        page = rows[offset:offset + limit]
        targets = {str(u.id): u.email for u in db.query(AppUser).filter(AppUser.id.in_([UUID(r.target_id) for r in page])).all()}
        items = [{"id": str(r.id), "target": targets.get(r.target_id, "Unavailable account"), "detail": policy.decode(r).get("reason", ""),
                  "kind": kind, "path": "/master/exceptions/" + str(r.id) + "/decision"} for r in page]
    return {"items": items, "total": total}


def deletion_state(db, user):
    profile = db.get(PersonalProfile, user.id)
    reports = db.query(PersonalReport).filter(PersonalReport.user_id == user.id).order_by(PersonalReport.id).all()
    grants = db.query(RoleGrant).filter(RoleGrant.user_id == user.id).all()
    value = [str(user.id), user.email, user.active, roles_version(grants), profile.version if profile else 0,
             [(str(r.id), r.version) for r in reports]]
    revision = hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()
    return profile, reports, grants, revision


@router.get("/accounts/{user_id}/deletion-preview")
def deletion_preview(user_id: UUID, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    user = db.get(AppUser, user_id)
    if not user:
        raise HTTPException(404, "Account not found")
    if policy.is_owner(db, user.id) or deleted(db, user.id):
        raise HTTPException(403, "This account is protected or already deleted")
    profile, reports, grants, revision = deletion_state(db, user)
    return {"id": str(user.id), "email": user.email, "revision": revision, "profile": bool(profile and profile.details_encrypted),
            "reports": len(reports), "permissions": len(grants), "official_records_retained": True, "auth_identity_retained": True}


class DeleteWorkspace(InputModel):
    confirmation_email: str = Field(min_length=3, max_length=320)
    expected_revision: str = Field(min_length=64, max_length=64)


@router.post("/accounts/{user_id}/delete-workspace")
def delete_workspace(user_id: UUID, body: DeleteWorkspace, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    lock_organization(db)
    user = lock_account(db, user_id)
    if policy.is_owner(db, user.id) or deleted(db, user.id):
        raise HTTPException(403, "This account is protected or already deleted")
    profile, reports, grants, revision = deletion_state(db, user)
    if revision != body.expected_revision or body.confirmation_email != user.email:
        raise HTTPException(409, "Account data changed or confirmation does not match; refresh deletion preview")
    supersede_access(db, actor, user.auth_sub)
    supersede_security(db, actor, user.id)
    for grant in grants:
        db.delete(grant)
    if profile:
        profile.details_encrypted = None
        profile.goals_encrypted = None
        profile.member_id = None
        profile.reviewer_id = None
        profile.version += 1
    for report in reports:
        report.content_encrypted = pack({"entries": [], "summary": "", "goals": []})
        report.review_note_encrypted = None
        report.status = "DRAFT"
        report.version += 1
    user.active = False
    user.email = "deleted-" + str(user.id) + "@deleted.invalid"
    for request in db.query(AccessRequest).filter(AccessRequest.auth_sub == user.auth_sub).all():
        request.email = user.email
    policy.event(db, actor, policy.POLICY_EVENT, user.id, {"exempt": False, "reason": "OMS workspace deleted"})
    policy.event(db, actor, "MASTER_ACCOUNT_DELETED", user.id, {"reports_cleared": len(reports), "grants_removed": len(grants), "official_history_retained": True})
    db.commit()
    return {"status": "DELETED", "auth_identity_retained": True, "official_records_retained": True}


@router.get("/activity")
def activity(limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0),
             actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    actions = [policy.POLICY_EVENT, policy.APPROVE_EVENT, policy.REJECT_EVENT, "MASTER_ACCOUNT_STATUS", "MASTER_ACCOUNT_DELETED",
               "ACCESS_APPROVED", "ACCESS_REJECTED", "ACCESS_SUPERSEDED", "CHANGE_APPROVED", "CHANGE_REJECTED", "PERSONAL_ASSIGNMENT_UPDATED", "MEMBERSHIP_CONFIRMED"]
    query = db.query(AuditLog).filter(AuditLog.action.in_(actions))
    total = query.count()
    rows = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(offset).limit(limit).all()
    actors = {u.id: u.email for u in db.query(AppUser).filter(AppUser.id.in_([r.actor_id for r in rows])).all()}
    return {"items": [{"id": str(r.id), "action": r.action, "target_id": r.target_id,
                       "actor": actors.get(r.actor_id, "Unavailable account"), "at": r.created_at.isoformat()} for r in rows], "total": total}
