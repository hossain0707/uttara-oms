"""Explicit owner confirmation/linking; never promotes a self-reported category silently."""
from datetime import date
from uuid import UUID, uuid4
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..auth import Actor, current_actor
from ..database import get_db
from ..models import AppUser, Member, PersonalProfile, AuditLog
from ..schemas import InputModel, MemberCreate, Category
from ..policies import lock_organization, active_unit
from ..security import normalize_phone, phone_digest
from .master import require_owner, lock_account
from .personal import unpack
from .directory import name_key, matches
from .members import create_member_record

router = APIRouter(prefix='/master', tags=['membership confirmation'])


def eligible(db, user_id):
    user = db.get(AppUser, user_id)
    profile = db.get(PersonalProfile, user_id)
    details = unpack(profile.details_encrypted) if profile else {}
    if not user or not user.active or not profile or not details.get('consent') or not (details.get('full_name') or '').strip():
        raise HTTPException(422, 'An active account with a saved, consented profile is required')
    return user, profile, details


def member_summary(db, member):
    linked = db.query(PersonalProfile.user_id).filter(PersonalProfile.member_id == member.id).first()
    return {'id': str(member.id), 'member_number': member.member_number, 'full_name': member.full_name,
            'category': member.category, 'org_node_id': str(member.org_node_id), 'status': member.status,
            'version': member.version, 'already_linked': linked is not None}


@router.get('/confirmation-queue')
def queue(q: str = Query(default='', max_length=120), limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0),
          actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    rows = db.query(PersonalProfile, AppUser).join(AppUser, AppUser.id == PersonalProfile.user_id).filter(
        AppUser.active.is_(True), PersonalProfile.member_id.is_(None), PersonalProfile.details_encrypted.is_not(None))
    terms = name_key(q).split()
    result = []
    for profile, user in rows.yield_per(20):
        details = unpack(profile.details_encrypted)
        name = details.get('full_name', '')
        if not details.get('consent') or not name.strip():
            continue
        if q.strip() and q.strip().casefold() not in user.email.casefold() and not (terms and matches(terms, name)):
            continue
        result.append({'id': str(user.id), 'email': user.email, 'full_name': name, 'category': details.get('category') or 'UNSPECIFIED'})
    result.sort(key=lambda r: (name_key(r['full_name']), r['id']))
    return {'items': result[offset:offset+limit], 'total': len(result)}


@router.get('/accounts/{user_id}/membership')
def preview(user_id: UUID, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    user, profile, details = eligible(db, user_id)
    if profile.member_id:
        member = db.get(Member, profile.member_id)
        return {'profile_version': profile.version, 'linked': member_summary(db, member), 'profile': None, 'matches': []}
    try:
        phone = normalize_phone(details.get('phone'))
    except ValueError:
        raise HTTPException(422, 'Ask the profile owner to correct their phone number first')
    digest = phone_digest(phone)
    candidates = []
    for member in db.query(Member).yield_per(50):
        same_phone = bool(digest and digest == member.phone_digest)
        same_name = name_key(member.full_name) == name_key(details['full_name'])
        if same_phone or same_name:
            candidates.append({**member_summary(db, member), 'match': 'PHONE' if same_phone else 'NAME'})
    return {'profile_version': profile.version, 'linked': None,
            'profile': {'full_name': details['full_name'], 'category': details.get('category') or '',
                        'occupation': details.get('occupation', ''), 'position': details.get('position', ''),
                        'phone_hint': '•••• ' + phone[-4:] if phone else 'Not added',
                        'requested_unit_id': details.get('requested_unit_id')}, 'matches': sorted(candidates, key=lambda m: (m['match'] != 'PHONE', m['member_number']))[:20],
            'matches_truncated': len(candidates) > 20}


class ConfirmMembership(InputModel):
    expected_profile_version: int = Field(ge=1)
    mode: Literal['CREATE', 'LINK']
    category: Category | None = None
    org_node_id: UUID | None = None
    member_number: str = Field(default='', max_length=48)
    joined_on: date | None = None
    member_id: UUID | None = None
    expected_member_version: int | None = Field(default=None, ge=1)
    consent_attested: Literal[True]
    duplicates_reviewed: Literal[True]


@router.post('/accounts/{user_id}/membership')
def confirm(user_id: UUID, body: ConfirmMembership, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    require_owner(db, actor)
    lock_organization(db)
    lock_account(db, user_id)
    user, profile, details = eligible(db, user_id)
    if profile.version != body.expected_profile_version:
        raise HTTPException(409, 'Profile or assignment changed; reload confirmation first')
    if profile.member_id:
        raise HTTPException(409, 'This account is already linked; no second member record was created')
    try:
        phone = normalize_phone(details.get('phone'))
    except ValueError:
        raise HTTPException(422, 'Ask the profile owner to correct their phone number first')
    digest = phone_digest(phone)
    existing_phone = db.query(Member).filter(Member.phone_digest == digest).first() if digest else None
    try:
        if body.mode == 'LINK':
            member = db.query(Member).filter(Member.id == body.member_id).with_for_update().one_or_none() if body.member_id else None
            if not member:
                raise HTTPException(422, 'Select an existing official member')
            if member.version != body.expected_member_version:
                raise HTTPException(409, 'Official member changed; reload before linking')
            if existing_phone and existing_phone.id != member.id:
                raise HTTPException(409, 'The saved phone matches a different official record; review that record')
            if member.status != 'ACTIVE' or not active_unit(db, member.org_node_id):
                raise HTTPException(422, 'Choose an active official member in an active unit, or correct its status first')
            if db.query(PersonalProfile).filter(PersonalProfile.member_id == member.id).first():
                raise HTTPException(409, 'This member is already linked to another account')
        else:
            if existing_phone:
                raise HTTPException(409, 'An official record already uses the saved phone. Review and link it instead')
            if not body.category or not body.org_node_id:
                raise HTTPException(422, 'Select the approved category and an active unit')
            number = body.member_number or 'OMS-' + uuid4().hex[:12].upper()
            if len(number.strip()) < 2 or len(details['full_name'].strip()) < 2:
                raise HTTPException(422, 'Member number and saved full name need at least two characters')
            payload = MemberCreate(member_number=number, full_name=details['full_name'], phone=phone,
                                   occupation=details.get('occupation') or None, position=details.get('position') or None,
                                   category=body.category, org_node_id=body.org_node_id, joined_on=body.joined_on,
                                   consent_attested=True, consent_version='owner-confirmation-v1')
            member = create_member_record(db, actor, payload)
        profile.member_id = member.id
        profile.version += 1
        db.add(AuditLog(actor_id=actor.id, action='MEMBERSHIP_CONFIRMED', target_id=str(user.id),
                        detail='mode=' + body.mode + ';member=' + str(member.id)))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, 'Member number, phone or account link already exists; refresh and review') from exc
    return {'status': 'CONFIRMED', 'member_id': str(member.id), 'created': body.mode == 'CREATE'}
