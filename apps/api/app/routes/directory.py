"""Authorized directory projection; never returns private profile documents/reports."""
import unicodedata
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..auth import Actor, current_actor
from ..database import get_db
from ..models import AppUser, AuditLog, Member, PersonalProfile
from ..policies import is_thana_admin, personal_nodes
from ..security import normalize_phone, phone_digest
from .members import view
from .personal import unpack

router = APIRouter(prefix="/directory", tags=["people directory"])


def name_key(value):
    # Normalize only for matching. Keep the original saved spelling in responses.
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = "".join("" if unicodedata.category(c) == "Cf" else c if unicodedata.category(c)[0] in "LMN" else " " for c in value)
    return " ".join(value.split())


def matches(terms, *values):
    keys = [name_key(v) for v in values if v]
    return not terms or all(any(term in key for key in keys) for term in terms)


@router.get("")
def directory(q: str = Query(default="", max_length=120), category: str | None = None,
              status: str | None = None, limit: int = Query(default=30, ge=1, le=100),
              offset: int = Query(default=0, ge=0), actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    global_access = is_thana_admin(actor)
    scopes = personal_nodes(db, actor)
    if not scopes:
        raise HTTPException(403, "No personal record access assigned")
    if category and category not in {"RUKON", "WORKER", "ASSOCIATE", "SUPPORTER"}:
        raise HTTPException(422, "Unknown category")
    if status and status not in {"ACTIVE", "INACTIVE"}:
        raise HTTPException(422, "Unknown status")
    terms = name_key(q).split()
    if q.strip() and not terms:
        terms = ["\x00"]  # Symbols-only queries cannot match a normalized name.
    phone = None
    try:
        phone = phone_digest(normalize_phone(q.translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"))))
    except ValueError:
        pass
    members = db.query(Member).filter(Member.org_node_id.in_(scopes)).all()
    by_id = {m.id: m for m in members}
    linked = {}
    profiles = []
    query = db.query(PersonalProfile, AppUser).join(AppUser, AppUser.id == PersonalProfile.user_id).filter(PersonalProfile.details_encrypted.is_not(None))
    # An untrusted requested unit never makes a private account visible to scoped staff.
    if not global_access:
        query = query.filter(PersonalProfile.member_id.in_(list(by_id)))
    for profile, account in query.yield_per(50):
        details = unpack(profile.details_encrypted)
        if not details.get("consent"):
            continue
        if profile.member_id:
            if profile.member_id in by_id:
                linked[profile.member_id] = (profile, details)
            continue
        full_name = details.get("full_name", "")
        if not full_name.strip() or not matches(terms, full_name):
            continue
        state = "ACTIVE" if account.active else "INACTIVE"
        if (category and details.get("category") != category) or (status and status != state):
            continue
        # Explicit allowlist. No phone, email, addresses, IDs, books or private dates.
        profiles.append({"source": "PROFILE", "id": "profile:" + str(profile.user_id), "member_number": "",
                         "full_name": full_name, "father_name": None, "phone": None, "address": None,
                         "occupation": details.get("occupation", ""), "position": details.get("position", ""),
                         "category": details.get("category", ""), "status": state, "org_node_id": "",
                         "joined_on": None, "version": 0, "self_reported": True,
                         "photo": details.get("photo", "") if details.get("directory_sharing") or profile.user_id == actor.id else ""})
    results = profiles
    for member in members:
        if (category and member.category != category) or (status and member.status != status):
            continue
        profile, details = linked.get(member.id, (None, {}))
        if not matches(terms, member.full_name, member.member_number, details.get("full_name")) and not (phone and member.phone_digest == phone):
            continue
        photo = details.get("photo", "") if details.get("directory_sharing") or (profile and profile.user_id == actor.id) else ""
        results.append({**view(member, photo), "source": "MEMBER", "self_reported": False})
    results.sort(key=lambda item: (name_key(item["full_name"]), item["source"], item["id"]))
    page = results[offset:offset + limit]
    db.add(AuditLog(actor_id=actor.id, action="UNIFIED_DIRECTORY_READ", target_id="directory", detail=f"offset={offset};limit={limit};returned={len(page)}"))
    db.commit()
    return {"items": page, "total": len(results)}
