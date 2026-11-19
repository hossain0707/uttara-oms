from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..auth import Actor, current_actor
from ..database import get_db
from ..models import AuditLog, Member, MemberEvent, OrgNode
from ..policies import allowed_nodes, require_scope
from ..schemas import MemberCreate, MemberRoutineUpdate
from ..security import decrypt, encrypt, normalize_phone, phone_digest

router = APIRouter(prefix="/members", tags=["members"])


def view(m: Member) -> dict:
    return {
        "id": str(m.id), "member_number": m.member_number, "full_name": m.full_name,
        "father_name": m.father_name, "phone": decrypt(m.phone_encrypted),
        "address": decrypt(m.address_encrypted), "occupation": m.occupation,
        "position": m.position, "category": m.category, "status": m.status,
        "org_node_id": str(m.org_node_id),
        "joined_on": m.joined_on.isoformat() if m.joined_on else None,
        "version": m.version,
    }


def visible(db: Session, actor: Actor, member_id: UUID, write=False) -> Member:
    m = db.get(Member, member_id)
    if not m:
        raise HTTPException(404, "Record not found")
    require_scope(db, actor, m.org_node_id, write=write)
    return m


@router.get("")
def list_members(q: str | None = Query(default=None, max_length=120),
                 category: str | None = None, status: str | None = None,
                 limit: int = Query(default=30, ge=1, le=100),
                 offset: int = Query(default=0, ge=0),
                 actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    scopes = allowed_nodes(db, actor)
    if not scopes:
        return {"items": [], "total": 0}
    query = db.query(Member).filter(Member.org_node_id.in_(scopes))
    if category:
        if category not in {"RUKON", "WORKER", "ASSOCIATE", "SUPPORTER"}:
            raise HTTPException(422, "Unknown category")
        query = query.filter(Member.category == category)
    if status:
        if status not in {"ACTIVE", "INACTIVE"}:
            raise HTTPException(422, "Unknown status")
        query = query.filter(Member.status == status)
    if q:
        search = q.strip()
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        phone = None
        try:
            phone = phone_digest(normalize_phone(search))
        except ValueError:
            pass
        conditions = [Member.full_name.ilike(f"%{escaped}%", escape="\\"),
                      Member.member_number.ilike(f"%{escaped}%", escape="\\")]
        if phone:
            conditions.append(Member.phone_digest == phone)
        query = query.filter(or_(*conditions))
    total = query.count()
    items = query.order_by(Member.full_name.asc(), Member.id.asc()).offset(offset).limit(limit).all()
    return {"items": [view(m) for m in items], "total": total}


@router.get("/{member_id}")
def get_member(member_id: UUID, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    return view(visible(db, actor, member_id))


@router.post("", status_code=201)
def add_member(payload: MemberCreate, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_scope(db, actor, payload.org_node_id, write=True)
    unit = db.get(OrgNode, payload.org_node_id)
    if not unit or unit.kind != "UNIT" or not unit.active:
        raise HTTPException(422, "Choose an active unit")
    try:
        phone = normalize_phone(payload.phone)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    member = Member(
        member_number=payload.member_number.strip(), full_name=payload.full_name.strip(),
        father_name=payload.father_name, phone_encrypted=encrypt(phone),
        phone_digest=phone_digest(phone), address_encrypted=encrypt(payload.address),
        occupation=payload.occupation, position=payload.position, category=payload.category,
        org_node_id=payload.org_node_id, joined_on=payload.joined_on,
        consent_at=datetime.now(timezone.utc), consent_version=payload.consent_version,
        status="ACTIVE",
    )
    try:
        db.add(member)
        db.flush()
        db.add(MemberEvent(member_id=member.id, action="CREATED", after="ACTIVE", actor_id=actor.id))
        db.add(AuditLog(actor_id=actor.id, action="MEMBER_CREATED", target_id=str(member.id)))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Member number or phone number already exists") from exc
    db.refresh(member)
    return view(member)


@router.patch("/{member_id}")
def update_routine(member_id: UUID, payload: MemberRoutineUpdate, actor: Actor = Depends(current_actor),
                   db: Session = Depends(get_db)):
    m = visible(db, actor, member_id, write=True)
    if m.version != payload.expected_version:
        raise HTTPException(409, "Record changed by another user; reload")
    data = payload.model_dump(exclude_unset=True, exclude={"expected_version"})
    if not data:
        raise HTTPException(422, "No routine fields to update")
    try:
        if "phone" in data:
            phone = normalize_phone(data.pop("phone"))
            m.phone_encrypted = encrypt(phone)
            m.phone_digest = phone_digest(phone)
        if "address" in data:
            m.address_encrypted = encrypt(data.pop("address"))
        for key, value in data.items():
            setattr(m, key, value)
        m.version += 1
        db.add(AuditLog(actor_id=actor.id, action="MEMBER_ROUTINE_UPDATED",
                        target_id=str(m.id), detail="Fields: " + ", ".join(sorted(payload.model_fields_set - {"expected_version"}))))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Phone number already exists") from exc
    db.refresh(m)
    return view(m)
