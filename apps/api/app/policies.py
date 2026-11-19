from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from .auth import Actor
from .models import OrgNode

ROLES = {"THANA_ADMIN", "THANA_VIEWER", "WARD_ADMIN", "UNIT_EDITOR"}
CATEGORIES = {"RUKON", "WORKER", "ASSOCIATE", "SUPPORTER"}
STATUSES = {"ACTIVE", "INACTIVE"}


def descendants(db: Session, root: UUID) -> set[UUID]:
    nodes = db.query(OrgNode).all()
    children: dict[UUID | None, list[UUID]] = {}
    for n in nodes:
        children.setdefault(n.parent_id, []).append(n.id)
    seen, stack = set(), [root]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(children.get(n, []))
    return seen


def allowed_nodes(db: Session, actor: Actor, *, write: bool = False) -> set[UUID]:
    nodes = db.query(OrgNode.id).all()
    all_ids = {n[0] for n in nodes}
    if any(role == "THANA_ADMIN" for role, _ in actor.grants):
        return all_ids
    if not write and any(role == "THANA_VIEWER" for role, _ in actor.grants):
        return all_ids
    scoped = set()
    for role, scope in actor.grants:
        if scope and role in ({"WARD_ADMIN", "UNIT_EDITOR"} if write else {"WARD_ADMIN", "UNIT_EDITOR"}):
            scoped |= descendants(db, scope) if role == "WARD_ADMIN" else {scope}
    return scoped & all_ids


def require_scope(db: Session, actor: Actor, node_id: UUID, *, write: bool = False):
    if node_id not in allowed_nodes(db, actor, write=write):
        raise HTTPException(403, "Insufficient organizational scope")


def is_thana_admin(actor: Actor) -> bool:
    return any(role == "THANA_ADMIN" for role, _ in actor.grants)


def can_approve(db: Session, actor: Actor, origin: UUID, dest: UUID | None = None) -> bool:
    if is_thana_admin(actor):
        return True
    for role, ward in actor.grants:
        if role == "WARD_ADMIN" and ward:
            scope = descendants(db, ward)
            if origin in scope and (dest is None or dest in scope):
                return True
    return False



def personal_nodes(db: Session, actor: Actor) -> set[UUID]:
    """PII scopes intentionally exclude THANA_VIEWER, even if another scoped role exists."""
    if is_thana_admin(actor):
        return {n[0] for n in db.query(OrgNode.id).all()}
    result = set()
    for role, node_id in actor.grants:
        if role == "WARD_ADMIN" and node_id:
            result |= descendants(db, node_id)
        elif role == "UNIT_EDITOR" and node_id:
            result.add(node_id)
    return result


def lock_organization(db: Session):
    """Serialize structural/membership writes against root; acquired before entity locks."""
    return (db.query(OrgNode).filter(OrgNode.kind == "THANA")
            .order_by(OrgNode.id).with_for_update().all())


def active_unit(db: Session, node_id: UUID) -> bool:
    node = db.get(OrgNode, node_id)
    if node is None or node.kind != "UNIT":
        return False
    seen = set()
    for kind in ("UNIT", "WARD", "THANA"):
        if node is None or node.kind != kind or not node.active or node.id in seen:
            return False
        seen.add(node.id)
        parent = node.parent_id
        if kind == "THANA":
            return parent is None
        node = db.get(OrgNode, parent) if parent else None
    return False
