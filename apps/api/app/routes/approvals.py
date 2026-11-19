from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..auth import Actor, current_actor
from ..database import get_db
from ..models import AuditLog, ChangeRequest, MemberEvent, OrgNode
from ..policies import CATEGORIES, can_approve, require_scope, allowed_nodes
from ..schemas import ChangeDecision, ChangePropose
from .members import visible

router = APIRouter(prefix="/approvals", tags=["approvals"])


def record(r: ChangeRequest):
    return {"id": str(r.id), "member_id": str(r.member_id), "kind": r.kind,
            "proposed_value": r.proposed_value, "status": r.status,
            "requested_by": str(r.requested_by), "requested_at": r.requested_at.isoformat(),
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            "review_note": r.review_note}


@router.get("")
def pending(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    from ..models import Member
    scopes = allowed_nodes(db, actor)
    rows = (db.query(ChangeRequest).join(Member, Member.id == ChangeRequest.member_id)
            .filter(Member.org_node_id.in_(scopes))
            .order_by(ChangeRequest.requested_at.desc()).limit(200).all())
    return {"items": [record(r) for r in rows]}


@router.post("/members/{member_id}", status_code=201)
def propose(member_id: UUID, body: ChangePropose, actor: Actor = Depends(current_actor),
            db: Session = Depends(get_db)):
    m = visible(db, actor, member_id, write=True)
    if body.kind == "CATEGORY":
        if body.proposed_value not in CATEGORIES or body.proposed_value == m.category:
            raise HTTPException(422, "Choose a different valid category")
    elif body.kind == "TRANSFER":
        try:
            destination = db.get(OrgNode, UUID(body.proposed_value))
        except ValueError:
            destination = None
        if not destination or not destination.active or destination.kind != "UNIT" or destination.id == m.org_node_id:
            raise HTTPException(422, "Choose a different active unit")
    elif body.kind == "DEACTIVATE":
        if m.status != "ACTIVE" or body.proposed_value != "INACTIVE":
            raise HTTPException(422, "Expected transition ACTIVE → INACTIVE")
    elif body.kind == "REACTIVATE":
        if m.status != "INACTIVE" or body.proposed_value != "ACTIVE":
            raise HTTPException(422, "Expected transition INACTIVE → ACTIVE")
    existing = db.query(ChangeRequest).filter(
        ChangeRequest.member_id == m.id, ChangeRequest.kind == body.kind,
        ChangeRequest.status == "PENDING").first()
    if existing:
        raise HTTPException(409, "A pending request of this type already exists")
    r = ChangeRequest(member_id=m.id, kind=body.kind,
                      proposed_value=body.proposed_value, original_version=m.version,
                      requested_by=actor.id)
    db.add(r)
    db.flush()
    db.add(AuditLog(actor_id=actor.id, action="CHANGE_PROPOSED", target_id=str(r.id), detail=body.kind))
    db.commit()
    db.refresh(r)
    return record(r)


@router.post("/{request_id}/decision")
def decide(request_id: UUID, body: ChangeDecision, actor: Actor = Depends(current_actor),
           db: Session = Depends(get_db)):
    from ..models import Member
    r = db.query(ChangeRequest).filter(ChangeRequest.id == request_id).with_for_update().one_or_none()
    if not r:
        raise HTTPException(404, "Request not found")
    if r.status != "PENDING":
        raise HTTPException(409, "Request already reviewed")
    m = db.query(Member).filter(Member.id == r.member_id).with_for_update().one()
    if r.requested_by == actor.id:
        raise HTTPException(403, "Self approval is prohibited")
    destination = UUID(r.proposed_value) if r.kind == "TRANSFER" else None
    if not can_approve(db, actor, m.org_node_id, destination):
        raise HTTPException(403, "Approver lacks required scope")
    if m.version != r.original_version and body.approve:
        raise HTTPException(409, "Member changed after submission; reject and resubmit")
    if body.approve:
        if r.kind == "CATEGORY":
            before = m.category
            m.category = r.proposed_value
            after = m.category
        elif r.kind == "TRANSFER":
            target = db.get(OrgNode, destination)
            if not target or target.kind != "UNIT" or not target.active:
                raise HTTPException(409, "Destination is no longer active")
            before = str(m.org_node_id)
            m.org_node_id = destination
            after = str(m.org_node_id)
        else:
            before = m.status
            m.status = r.proposed_value
            after = m.status
        m.version += 1
        db.add(MemberEvent(member_id=m.id, action=r.kind,
                           before=before, after=after, actor_id=actor.id))
    r.status = "APPROVED" if body.approve else "REJECTED"
    r.reviewed_by = actor.id
    r.review_note = body.note
    r.reviewed_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor_id=actor.id, action="CHANGE_" + r.status, target_id=str(r.id),
                    detail=r.kind))
    db.commit()
    db.refresh(r)
    return record(r)
