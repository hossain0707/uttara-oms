"""Role access changes: two distinct Thana Admin users must approve sensitive grants."""
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..auth import Actor, current_actor
from ..database import get_db
from ..models import AccessRequest, AppUser, AuditLog, OrgNode, RoleGrant
from ..policies import ROLES, is_thana_admin, lock_organization

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
    return {"items": [
        {"id": str(u.id), "auth_sub": u.auth_sub, "email": u.email,
         "active": u.active,
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
    if not global_role:
        scope = db.get(OrgNode, data.scope_node_id) if data.scope_node_id else None
        expected = "WARD" if data.role == "WARD_ADMIN" else "UNIT"
        if not scope or not scope.active or scope.kind != expected:
            raise HTTPException(422, "Select an active matching scope")
    subject = str(data.auth_sub)
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
    db.commit(); db.refresh(row)
    return summary(row)


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
    if actor.id == row.requested_by:
        raise HTTPException(403, "Independent administrator approval required")
    if body.approve:
        user = db.query(AppUser).filter(AppUser.auth_sub == row.auth_sub).with_for_update().one_or_none()
        if row.operation == "GRANT":
            if row.role in {"WARD_ADMIN", "UNIT_EDITOR"}:
                scope = db.get(OrgNode, row.scope_node_id)
                expected = "WARD" if row.role == "WARD_ADMIN" else "UNIT"
                if not scope or not scope.active or scope.kind != expected:
                    raise HTTPException(409, "Requested scope is no longer active")
            if user is None:
                user = AppUser(auth_sub=row.auth_sub, email=row.email, active=True)
                db.add(user); db.flush()
            else:
                user.active = True
            existing = db.query(RoleGrant).filter(
                RoleGrant.user_id == user.id, RoleGrant.role == row.role,
                RoleGrant.scope_node_id == row.scope_node_id,
            ).first()
            if existing:
                raise HTTPException(409, "Role already granted")
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
                remaining = (db.query(RoleGrant.user_id).join(AppUser, AppUser.id == RoleGrant.user_id)
                             .filter(RoleGrant.role == "THANA_ADMIN", AppUser.active.is_(True)).distinct().count())
                if remaining <= 2:
                    raise HTTPException(409, "Maintain two administrators for independent approvals")
            db.delete(grant)
    row.status = "APPROVED" if body.approve else "REJECTED"
    row.reviewed_by = actor.id
    row.reviewed_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor_id=actor.id, action="ACCESS_" + row.status,
                    target_id=str(row.id), detail=row.operation + ":" + row.role))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Concurrent access modification; review again") from exc
    db.refresh(row)
    return summary(row)
