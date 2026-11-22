"""Role access changes: two distinct Thana Admin users must approve sensitive grants."""
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..auth import Actor, current_actor, account_actor
from ..database import get_db
from ..models import AccessRequest, AppUser, AuditLog, OrgNode, RoleGrant
from .. import security_policy as policy
from ..owner_controls import direct_owner, deleted
from ..policies import ROLES, is_thana_admin, lock_organization, active_unit

router = APIRouter(prefix="/access", tags=["access control"])


class GrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    auth_sub: UUID
    email: str = Field(min_length=3, max_length=320)
    role: str
    scope_node_id: UUID | None = None
    operation: str = "GRANT"

    @field_validator("email")
    @classmethod
    def email_address(cls, v: str):
        if "@" not in v or v.count("@") != 1:
            raise ValueError("Invalid identity email")
        return v.strip().lower()

    @field_validator("role")
    @classmethod
    def allowed_role(cls, v: str):
        if v not in ROLES:
            raise ValueError("Unknown role")
        return v

    @field_validator("operation")
    @classmethod
    def allowed_operation(cls, v: str):
        if v not in {"GRANT", "REVOKE"}:
            raise ValueError("Unknown access operation")
        return v


class AccessDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approve: bool


def active_scope(db: Session, scope: OrgNode | None, role: str):
    if not scope or not scope.active: return False
    if role == "UNIT_EDITOR": return active_unit(db, scope.id)
    root = db.get(OrgNode, scope.parent_id) if scope.parent_id else None
    return scope.kind == "WARD" and bool(root and root.active and root.kind == "THANA" and root.parent_id is None)


def require_admin(actor: Actor):
    if not is_thana_admin(actor):
        raise HTTPException(403, "Thana Admin required")


def summary(r: AccessRequest):
    return {
        "id": str(r.id), "auth_sub": r.auth_sub, "email": r.email,
        "role": r.role, "scope_node_id": str(r.scope_node_id) if r.scope_node_id else None,
        "operation": r.operation, "status": r.status,
        "requested_by": str(r.requested_by), "requested_at": r.requested_at.isoformat(),
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
    }


@router.get("/users")
def users(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_admin(actor)
    all_users = db.query(AppUser).order_by(AppUser.email).limit(500).all()
    all_grants = db.query(RoleGrant).all()
    owner_uuid = policy.owner_id(db)
    return {"items": [
        {"id": str(u.id), "auth_sub": u.auth_sub, "email": u.email,
         "active": u.active, "is_master_admin": str(u.id) == owner_uuid,
         "roles": [{"role": r.role, "scope_node_id": str(r.scope_node_id) if r.scope_node_id else None}
                   for r in all_grants if r.user_id == u.id]}
        for u in all_users
    ]}


@router.get("/requests")
def requests(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_admin(actor)
    rows = db.query(AccessRequest).order_by(AccessRequest.requested_at.desc()).limit(200).all()
    return {"items": [summary(r) for r in rows]}


@router.post("/requests", status_code=201)
def request_access(data: GrantRequest, actor: Actor = Depends(current_actor),
                   db: Session = Depends(get_db)):
    require_admin(actor)
    lock_organization(db)
    global_role = data.role in {"THANA_ADMIN", "THANA_VIEWER"}
    if global_role and data.scope_node_id is not None:
        raise HTTPException(422, "Thana-level roles must not have a scope")
    if not global_role and data.operation == "GRANT":
        scope = db.get(OrgNode, data.scope_node_id) if data.scope_node_id else None
        if not active_scope(db, scope, data.role):
            raise HTTPException(422, "Select an active matching scope")
    subject = str(data.auth_sub)
    if data.operation == "REVOKE":
        target = db.query(AppUser).filter(AppUser.auth_sub == subject).first()
        if not target or not db.query(RoleGrant).filter(
            RoleGrant.user_id == target.id, RoleGrant.role == data.role,
            RoleGrant.scope_node_id == data.scope_node_id,
        ).first():
            raise HTTPException(409, "This permission is no longer assigned. Refresh the account directory.")
    duplicate = db.query(AccessRequest).filter(
        AccessRequest.auth_sub == subject,
        AccessRequest.role == data.role,
        AccessRequest.operation == data.operation,
        AccessRequest.status == "PENDING",
        AccessRequest.scope_node_id == data.scope_node_id,
    ).first()
    if duplicate and duplicate.scope_node_id == data.scope_node_id:
        raise HTTPException(409, "Equivalent change already pending")
    row = AccessRequest(auth_sub=subject, email=data.email, role=data.role,
                        scope_node_id=data.scope_node_id, operation=data.operation,
                        requested_by=actor.id)
    db.add(row); db.flush()
    db.add(AuditLog(actor_id=actor.id, action="ACCESS_REQUESTED",
                    target_id=str(row.id), detail=data.operation + ":" + data.role))
    if direct_owner(db, actor):
        apply_access_decision(db, actor, row, True)
    db.commit(); db.refresh(row)
    return summary(row)


def apply_access_decision(db, actor, row, approve):
    if approve:
        user = db.query(AppUser).filter(AppUser.auth_sub == row.auth_sub).with_for_update().one_or_none()
        if row.operation == "GRANT":
            if row.role in {"WARD_ADMIN", "UNIT_EDITOR"}:
                scope = db.get(OrgNode, row.scope_node_id)
                if not active_scope(db, scope, row.role):
                    raise HTTPException(409, "Requested scope is no longer active")
            if user is not None and deleted(db, user.id):
                raise HTTPException(409, "Deleted OMS accounts cannot receive permissions")
            if user is None:
                user = AppUser(auth_sub=row.auth_sub, email=row.email, active=True)
                db.add(user); db.flush()
            elif not user.active:
                raise HTTPException(409, "Master Admin must reactivate this suspended account first")
            existing = db.query(RoleGrant).filter(
                RoleGrant.user_id == user.id, RoleGrant.role == row.role,
                RoleGrant.scope_node_id == row.scope_node_id,
            ).first()
            if not existing:
                db.add(RoleGrant(user_id=user.id, role=row.role, scope_node_id=row.scope_node_id))
        else:
            if not user:
                raise HTTPException(404, "Target user not found")
            grant = db.query(RoleGrant).filter(
                RoleGrant.user_id == user.id, RoleGrant.role == row.role,
                RoleGrant.scope_node_id == row.scope_node_id,
            ).first()
            if not grant:
                raise HTTPException(404, "Target role not found")
            if row.role == "THANA_ADMIN":
                if policy.is_owner(db, user.id):
                    raise HTTPException(403, "The Master Admin role is protected from removal")
                remaining = (db.query(RoleGrant.user_id).join(AppUser, AppUser.id == RoleGrant.user_id)
                             .filter(RoleGrant.role == "THANA_ADMIN", AppUser.active.is_(True)).distinct().count())
                if remaining <= 2 and not direct_owner(db, actor):
                    raise HTTPException(409, "Maintain two administrators for independent approvals")
            db.delete(grant)
    row.status = "APPROVED" if approve else "REJECTED"
    row.reviewed_by = actor.id
    row.reviewed_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor_id=actor.id, action="ACCESS_" + row.status,
                    target_id=str(row.id), detail=row.operation + ":" + row.role))
    db.flush()


@router.post("/requests/{request_id}/decision")
def decide_access(request_id: UUID, body: AccessDecision,
                  actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_admin(actor)
    lock_organization(db)
    row = db.query(AccessRequest).filter(AccessRequest.id == request_id).with_for_update().one_or_none()
    if not row:
        raise HTTPException(404, "Request not found")
    if row.status != "PENDING":
        raise HTTPException(409, "Request already reviewed")
    if body.approve and actor.id == row.requested_by and not direct_owner(db, actor):
        raise HTTPException(403, "A different main administrator must approve a request you created. You can reject it instead.")
    apply_access_decision(db, actor, row, body.approve)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Concurrent access modification; review again") from exc
    db.refresh(row)
    return summary(row)


class AccessApplication(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str
    scope_node_id: UUID | None = None


@router.get("/my-requests")
def my_requests(actor: Actor = Depends(account_actor), db: Session = Depends(get_db)):
    user = db.get(AppUser, actor.id)
    return {"items": [summary(r) for r in db.query(AccessRequest).filter(
        AccessRequest.auth_sub == user.auth_sub).order_by(AccessRequest.requested_at.desc()).limit(100).all()]}


@router.post("/apply", status_code=201)
def apply_access(body: AccessApplication, actor: Actor = Depends(account_actor), db: Session = Depends(get_db)):
    if body.role not in {"THANA_VIEWER", "WARD_ADMIN", "UNIT_EDITOR"}:
        raise HTTPException(422, "Only responsible-person roles can be requested")
    lock_organization(db)
    if body.role == "THANA_VIEWER":
        if body.scope_node_id is not None: raise HTTPException(422, "Thana role must not have a scope")
    else:
        node = db.get(OrgNode, body.scope_node_id) if body.scope_node_id else None
        if not active_scope(db, node, body.role):
            raise HTTPException(422, "Choose an active matching scope")
    user = db.get(AppUser, actor.id)
    if db.query(RoleGrant).filter(RoleGrant.user_id == actor.id, RoleGrant.role == body.role,
                                  RoleGrant.scope_node_id == body.scope_node_id).first():
        raise HTTPException(409, "You already have this permission")
    if db.query(AccessRequest).filter(AccessRequest.auth_sub == user.auth_sub, AccessRequest.role == body.role,
        AccessRequest.scope_node_id == body.scope_node_id, AccessRequest.status == "PENDING").first():
        raise HTTPException(409, "Your request is already pending")
    row = AccessRequest(auth_sub=user.auth_sub, email=user.email, role=body.role,
        scope_node_id=body.scope_node_id, operation="GRANT", requested_by=actor.id)
    db.add(row); db.flush()
    db.add(AuditLog(actor_id=actor.id,action="ACCESS_APPLIED",target_id=str(row.id),detail=body.role))
    db.commit(); db.refresh(row)
    return summary(row)
