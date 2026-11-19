from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..auth import Actor, current_actor
from ..database import get_db
from ..models import AuditLog, Member, OrgNode
from ..policies import allowed_nodes, is_thana_admin
from ..schemas import OrgCreate, OrgUpdate

router = APIRouter(prefix="/organization", tags=["organization"])


def node_dict(n):
    return {"id": str(n.id), "parent_id": str(n.parent_id) if n.parent_id else None,
            "kind": n.kind, "code": n.code, "name": n.name, "active": n.active}


@router.get("/nodes")
def nodes(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    ids = allowed_nodes(db, actor)
    records = db.query(OrgNode).filter(OrgNode.id.in_(ids)).order_by(OrgNode.kind, OrgNode.code).all()
    return {"items": [node_dict(n) for n in records]}


@router.post("/nodes", status_code=201)
def create_node(body: OrgCreate, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    if not is_thana_admin(actor):
        raise HTTPException(403, "Thana Admin required")
    if body.kind == "THANA":
        if body.parent_id is not None or db.query(OrgNode).filter(OrgNode.kind == "THANA").count():
            raise HTTPException(422, "Only one root Thana is allowed")
    else:
        parent = db.get(OrgNode, body.parent_id) if body.parent_id else None
        expected = "THANA" if body.kind == "WARD" else "WARD"
        if not parent or parent.kind != expected or not parent.active:
            raise HTTPException(422, f"{body.kind} requires an active {expected} parent")
    n = OrgNode(**body.model_dump())
    try:
        db.add(n)
        db.flush()
        db.add(AuditLog(actor_id=actor.id, action="ORG_CREATED", target_id=str(n.id)))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Duplicate organizational code") from exc
    db.refresh(n)
    return node_dict(n)


@router.patch("/nodes/{node_id}")
def update_node(node_id: UUID, body: OrgUpdate, actor: Actor = Depends(current_actor),
                db: Session = Depends(get_db)):
    if not is_thana_admin(actor):
        raise HTTPException(403, "Thana Admin required")
    n = db.get(OrgNode, node_id)
    if not n:
        raise HTTPException(404, "Node not found")
    changes = body.model_dump(exclude_unset=True)
    if changes.get("active") is False:
        child_count = db.query(OrgNode).filter(OrgNode.parent_id == n.id, OrgNode.active.is_(True)).count()
        member_count = db.query(Member).filter(Member.org_node_id == n.id, Member.status == "ACTIVE").count()
        if child_count or member_count:
            raise HTTPException(409, "Deactivate dependent units and relocate active members first")
    for field, value in changes.items():
        setattr(n, field, value)
    db.add(AuditLog(actor_id=actor.id, action="ORG_UPDATED", target_id=str(n.id),
                    detail=", ".join(sorted(changes))))
    db.commit()
    db.refresh(n)
    return node_dict(n)
