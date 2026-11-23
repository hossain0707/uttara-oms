"""Owner-only personal workspace and explicitly assigned report review."""

import base64
import binascii
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import calendar
import json
from datetime import date, datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, model_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..auth import Actor, account_actor, current_actor
from ..database import get_db
from ..models import (
    AppUser,
    AuditLog,
    Member,
    OrgNode,
    PersonalProfile,
    PersonalReport,
    RoleGrant,
)
from ..schemas import InputModel
from ..security import decrypt, encrypt, normalize_phone
from ..policies import is_thana_admin, active_unit

from ..report_fields import METRICS, EXTRA, REFLECTIONS, aggregate

router = APIRouter(tags=["personal workspace"])



def unpack(value):
    return json.loads(decrypt(value)) if value else {}


def pack(value):
    return encrypt(json.dumps(value, ensure_ascii=False))


def audit(db, actor, action, target):
    db.add(AuditLog(actor_id=actor.id, action=action, target_id=str(target)))


def lock_user(db, user_id):
    db.query(AppUser).filter(AppUser.id == user_id).with_for_update().one()


class Book(InputModel):
    title: str = Field(min_length=1, max_length=250)
    total_pages: int = Field(default=0, ge=0, le=100000)
    completed_pages: int = Field(default=0, ge=0, le=100000)

    @model_validator(mode="after")
    def pages(self):
        if self.total_pages and self.completed_pages > self.total_pages:
            raise ValueError("Completed pages exceed the book length")
        return self


class ProfileData(InputModel):
    # Compatibility input only; discarded, never returned or saved.
    identity_type: Literal["", "NID", "PASSPORT"] = ""
    identity_number: str = Field(default="", max_length=30)
    photo: str = Field(default="", max_length=160000)
    directory_sharing: bool = False
    full_name: str = Field(default="", max_length=200)
    father_name: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=40)
    current_address: str = Field(default="", max_length=1000)
    permanent_address: str = Field(default="", max_length=1000)
    occupation: str = Field(default="", max_length=160)
    position: str = Field(default="", max_length=160)
    requested_unit_id: UUID | None = None
    category: Literal["", "RUKON", "WORKER", "ASSOCIATE", "SUPPORTER"] = ""
    joined_on: date | None = None
    worker_since: date | None = None
    candidate_since: date | None = None
    oath_on: date | None = None
    books: list[Book] = Field(default_factory=list, max_length=100)
    consent: Literal[True]


    @model_validator(mode="after")
    def validate_photo(self):
        if self.photo:
            if not self.photo.startswith("data:image/jpeg;base64,"):
                raise ValueError("Choose a JPEG profile photo")
            try:
                raw = base64.b64decode(self.photo.split(",", 1)[1], validate=True)
                if len(raw) > 110000:
                    raise ValueError("Profile photo is too large")
                with Image.open(BytesIO(raw)) as image:
                    if image.format != "JPEG" or not (1 <= image.width <= 512 and 1 <= image.height <= 512):
                        raise ValueError("Profile photo must be a JPEG up to 512 pixels")
                    image.load()
                    # Re-encode rather than persist EXIF, location or appended data.
                    output = BytesIO()
                    clean = image.convert("RGB")
                    clean.thumbnail((384, 384))
                    clean.save(output, format="JPEG", quality=82)
                    if len(output.getvalue()) > 110000:
                        raise ValueError("Profile photo is too large")
                self.photo = "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode()
            except (binascii.Error, OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
                raise ValueError("Choose a valid JPEG profile photo") from exc
        return self


class ProfileSave(InputModel):
    section: Literal["profile", "reading"] = "profile"
    expected_version: int = Field(ge=0)
    details: ProfileData


class Goal(InputModel):
    metric: Literal["prayers", "literature", "organization", "quran", "hadith"]
    target: int = Field(ge=1, le=1000000)


class Assignment(InputModel):
    expected_version: int = Field(ge=0)
    reviewer_id: UUID | None = None
    member_id: UUID | None = None
    goals: list[Goal] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def unique(self):
        if len({g.metric for g in self.goals}) != len(self.goals):
            raise ValueError("Each metric can have only one target")
        return self


class Entry(InputModel):
    day: date
    prayers: int | None = Field(default=None, ge=0, le=5)
    literature: int | None = Field(default=None, ge=0, le=100000)
    organization: int | None = Field(default=None, ge=0, le=1440)
    quran: int | None = Field(default=None, ge=0, le=100000)
    hadith: int | None = Field(default=None, ge=0, le=100000)
    congregational_prayers: int | None = Field(default=None, ge=0, le=5)
    quran_studied: bool | None = Field(default=None, strict=True)
    dawah_meetings: int | None = Field(default=None, ge=0, le=100000)
    worker_meetings: int | None = Field(default=None, ge=0, le=100000)
    member_meetings: int | None = Field(default=None, ge=0, le=100000)
    worker_contacts: int | None = Field(default=None, ge=0, le=100000)
    books_distributed: int | None = Field(default=None, ge=0, le=100000)
    family_meeting: bool | None = Field(default=None, strict=True)
    social_work: bool | None = Field(default=None, strict=True)
    donated_hours: float | None = Field(default=None, ge=0, le=24, multiple_of=0.01)
    visits: int | None = Field(default=None, ge=0, le=100000)
    report_kept: bool | None = Field(default=None, strict=True)
    self_evaluation: bool | None = Field(default=None, strict=True)
    notes: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def congregation(self):
        if self.congregational_prayers is not None and (self.prayers is None or self.congregational_prayers > self.prayers):
            raise ValueError("Enter total Salah first; congregational Salah cannot exceed total Salah")
        return self


class ReportSave(InputModel):
    month: date
    expected_version: int = Field(ge=0)
    entries: list[Entry] = Field(default_factory=list, max_length=31)
    summary: str = Field(default="", max_length=2000)
    achievements: str = Field(default="", max_length=2000)
    incomplete_work: str = Field(default="", max_length=2000)
    next_plan: str = Field(default="", max_length=2000)
    submit: bool = False
    consent: Literal[True]

    @model_validator(mode="after")
    def dates(self):
        today = datetime.now(ZoneInfo("Asia/Dhaka")).date()
        if self.month.day != 1 or self.month > today:
            raise ValueError("Choose the first day of a current or previous month")
        if len({e.day for e in self.entries}) != len(self.entries):
            raise ValueError("Only one entry per calendar day is allowed")
        if any(
            e.day.year != self.month.year
            or e.day.month != self.month.month
            or e.day > today
            for e in self.entries
        ):
            raise ValueError(
                "Entries must belong to the selected month and cannot be in the future"
            )
        if self.submit and not self.entries:
            raise ValueError("Add daily entries before submitting")
        return self


class Review(InputModel):
    expected_version: int = Field(ge=1)
    decision: Literal["REVIEWED", "RETURNED"]
    note: str = Field(min_length=1, max_length=2000)


def profile_view(row):
    return {
        "version": row.version if row else 0,
        "details": reviewer_profile(row) if row else {},
        "goals": unpack(row.goals_encrypted).get("items", []) if row else [],
        "reviewer_assigned": bool(row and row.reviewer_id),
        "member_linked": bool(row and row.member_id),
    }


def reviewer_profile(row):
    # Deprecated identity fields are excluded from every profile response.
    return {k: v for k, v in unpack(row.details_encrypted).items()
            if k not in {"identity_number", "identity_type"}}


def report_view(row, profile):
    content = unpack(row.content_encrypted)
    entries = content.get("entries", [])
    totals, reported_days = aggregate(entries)
    goals = content.get(
        "goals", unpack(profile.goals_encrypted).get("items", []) if profile else []
    )
    return {
        "id": str(row.id),
        "month": row.month.isoformat(),
        "status": row.status,
        "version": row.version,
        **content,
        "totals": totals,
        "reported_days": reported_days,
        **{key: content.get(key, "") for key in REFLECTIONS},
        "entered_days": len(entries),
        "calendar_days": calendar.monthrange(row.month.year, row.month.month)[1],
        "progress": [
            {
                **g,
                "actual": totals[g["metric"]],
                "remaining": max(0, g["target"] - totals[g["metric"]]),
                "unit": METRICS[g["metric"]],
            }
            for g in goals
        ],
        "review_note": decrypt(row.review_note_encrypted),
        "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
    }


@router.get("/self/profile")
def own_profile(actor: Actor = Depends(account_actor), db: Session = Depends(get_db)):
    row = db.get(PersonalProfile, actor.id)
    audit(db, actor, "SELF_PROFILE_READ", actor.id)
    db.commit()
    return profile_view(row)


@router.put("/self/profile")
def save_profile(
    body: ProfileSave,
    actor: Actor = Depends(account_actor),
    db: Session = Depends(get_db),
):
    lock_user(db, actor.id)
    row = db.get(PersonalProfile, actor.id)
    if (row.version if row else 0) != body.expected_version:
        raise HTTPException(409, "Profile changed; reload before saving")
    if body.details.requested_unit_id and not active_unit(
        db, body.details.requested_unit_id
    ):
        raise HTTPException(422, "Choose an active unit")
    details = body.details.model_dump(mode="json", exclude={"identity_number", "identity_type"})
    if body.section == "reading":
        previous = unpack(row.details_encrypted) if row else {}
        if not previous.get("consent"):
            raise HTTPException(422, "Save your profile and consent first")
        details = {**previous, "books": details["books"]}
    elif not details["full_name"].strip():
        raise HTTPException(422, "Enter your full name")
    details.pop("identity_number", None)
    details.pop("identity_type", None)
    try:
        details["phone"] = normalize_phone(details["phone"]) or ""
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if body.section == "profile":
        details["consent_at"] = datetime.now(timezone.utc).isoformat()
        details["consent_version"] = "personal-v3"
    if row is None:
        row = PersonalProfile(user_id=actor.id, version=0)
        db.add(row)
    row.details_encrypted = pack(details)
    row.version += 1
    row.updated_at = datetime.now(timezone.utc)
    audit(db, actor, "SELF_PROFILE_UPDATED", actor.id)
    db.commit()
    return profile_view(row)


@router.get("/self/organization")
def own_org(actor: Actor = Depends(account_actor), db: Session = Depends(get_db)):
    rows = db.query(OrgNode).filter(OrgNode.active.is_(True)).all()
    return {
        "items": [
            {
                "id": str(n.id),
                "parent_id": str(n.parent_id) if n.parent_id else None,
                "kind": n.kind,
                "name": n.name,
            }
            for n in rows
        ]
    }


@router.get("/self/reports")
def own_reports(actor: Actor = Depends(account_actor), db: Session = Depends(get_db)):
    profile = db.get(PersonalProfile, actor.id)
    rows = (
        db.query(PersonalReport)
        .filter(PersonalReport.user_id == actor.id)
        .order_by(PersonalReport.month.desc())
        .limit(120)
        .all()
    )
    audit(db, actor, "SELF_REPORTS_READ", actor.id)
    db.commit()
    return {"items": [report_view(r, profile) for r in rows], "metric_units": METRICS}


@router.put("/self/reports")
def save_report(
    body: ReportSave,
    actor: Actor = Depends(account_actor),
    db: Session = Depends(get_db),
):
    lock_user(db, actor.id)
    row = (
        db.query(PersonalReport)
        .filter(PersonalReport.user_id == actor.id, PersonalReport.month == body.month)
        .one_or_none()
    )
    if (row.version if row else 0) != body.expected_version:
        raise HTTPException(409, "Report changed; reload before saving")
    if row and row.status not in {"DRAFT", "RETURNED"}:
        raise HTTPException(409, "Submitted reports must be returned before editing")
    profile = db.get(PersonalProfile, actor.id)
    if not profile or not profile.details_encrypted:
        raise HTTPException(422, "Save your profile and consent first")
    if body.submit and not profile.reviewer_id:
        raise HTTPException(
            422, "Ask the main administrator to assign your reviewer before submitting"
        )
    if body.submit:
        reviewer = db.get(AppUser, profile.reviewer_id)
        if (
            not reviewer
            or not reviewer.active
            or not db.query(RoleGrant).filter(RoleGrant.user_id == reviewer.id).first()
        ):
            raise HTTPException(
                422,
                "Your reviewer is unavailable; ask the main administrator to reassign",
            )
    if row is None:
        row = PersonalReport(user_id=actor.id, month=body.month, version=0)
        db.add(row)
    previous = unpack(row.content_encrypted) if row.content_encrypted else {}
    previous_days = {e['day']:e for e in previous.get('entries', [])}
    saved_entries=[]
    for entry in body.entries:
        value=entry.model_dump(mode="json")
        old=previous_days.get(value['day'],{})
        # Older clients must not erase new activity fields when updating core values.
        for key in EXTRA:
            if key not in entry.model_fields_set and key in old:
                value[key]=old[key]
        # Recheck the merged record too, including fields preserved from older clients.
        try:
            Entry.model_validate(value)
        except ValueError as exc:
            raise HTTPException(422, "Correct Salah totals or congregational Salah in the existing day before saving") from exc
        saved_entries.append(value)
    row.content_encrypted = pack({
        "entries": saved_entries, "summary": body.summary,
        **{key:getattr(body,key) if key in body.model_fields_set else previous.get(key,"") for key in REFLECTIONS},
        "consent_version":"personal-report-v2", "goals":unpack(profile.goals_encrypted).get("items", []),
    })
    row.status = "SUBMITTED" if body.submit else "DRAFT"
    row.version += 1
    row.updated_at = datetime.now(timezone.utc)
    if body.submit:
        row.submitted_at = datetime.now(timezone.utc)
    db.flush()
    audit(db, actor, "PERSONAL_REPORT_" + row.status, row.id)
    db.commit()
    return report_view(row, profile)


@router.get("/reviews")
def review_queue(actor: Actor = Depends(current_actor), db: Session = Depends(get_db)):
    profiles = (
        db.query(PersonalProfile).filter(PersonalProfile.reviewer_id == actor.id).all()
    )
    ids = [p.user_id for p in profiles if p.user_id != actor.id]
    reports = (
        db.query(PersonalReport)
        .filter(PersonalReport.user_id.in_(ids), PersonalReport.status == "SUBMITTED")
        .order_by(PersonalReport.month)
        .limit(200)
        .all()
    )
    users = {u.id: u.email for u in db.query(AppUser).filter(AppUser.id.in_(ids)).all()}
    audit(db, actor, "ASSIGNED_REPORT_QUEUE_READ", "reports")
    db.commit()
    return {
        "items": [
            {
                **report_view(r, next(p for p in profiles if p.user_id == r.user_id)),
                "email": users[r.user_id],
                "profile": reviewer_profile(next(p for p in profiles if p.user_id == r.user_id)),
            }
            for r in reports
        ]
    }


@router.post("/reviews/{report_id}")
def review_report(
    report_id: UUID,
    body: Review,
    actor: Actor = Depends(current_actor),
    db: Session = Depends(get_db),
):
    found = db.get(PersonalReport, report_id)
    if not found:
        raise HTTPException(404, "Report not found")
    lock_user(db, found.user_id)
    row = (
        db.query(PersonalReport)
        .filter(PersonalReport.id == report_id)
        .populate_existing()
        .with_for_update()
        .one_or_none()
    )
    profile = db.get(PersonalProfile, row.user_id) if row else None
    if (
        not row
        or not profile
        or profile.reviewer_id != actor.id
        or row.user_id == actor.id
    ):
        raise HTTPException(
            403, "Only the assigned independent reviewer can review this report"
        )
    if row.status != "SUBMITTED" or row.version != body.expected_version:
        raise HTTPException(409, "Report is no longer awaiting this review; reload")
    row.status = body.decision
    row.review_note_encrypted = encrypt(body.note)
    row.reviewed_by = actor.id
    row.reviewed_at = datetime.now(timezone.utc)
    row.version += 1
    audit(db, actor, "PERSONAL_REPORT_" + body.decision, row.id)
    db.commit()
    return {"status": row.status}


@router.put("/access/personal/{user_id}")
def assign_personal(
    user_id: UUID,
    body: Assignment,
    actor: Actor = Depends(current_actor),
    db: Session = Depends(get_db),
):
    if not is_thana_admin(actor):
        raise HTTPException(403, "Main administrator required")
    user = db.get(AppUser, user_id)
    if not user or not user.active:
        raise HTTPException(404, "Active account not found")
    lock_user(db, user_id)
    if body.reviewer_id:
        reviewer = db.get(AppUser, body.reviewer_id)
        role = db.query(RoleGrant).filter(RoleGrant.user_id == body.reviewer_id).first()
        if (
            body.reviewer_id == user_id
            or not reviewer
            or not reviewer.active
            or not role
        ):
            raise HTTPException(
                422,
                "Assign a different active responsible person with an organizational role",
            )
    if body.member_id and not db.get(Member, body.member_id):
        raise HTTPException(404, "Member not found")
    if body.member_id:
        linked = (
            db.query(PersonalProfile)
            .filter(
                PersonalProfile.member_id == body.member_id,
                PersonalProfile.user_id != user_id,
            )
            .first()
        )
        if linked:
            raise HTTPException(409, "This person is linked to another account")
    row = db.get(PersonalProfile, user_id)
    if (row.version if row else 0) != body.expected_version:
        raise HTTPException(409, "Profile changed; reload")
    if row is None:
        row = PersonalProfile(user_id=user_id, version=0)
        db.add(row)
    row.reviewer_id = body.reviewer_id
    row.member_id = body.member_id
    row.goals_encrypted = pack({"items": [g.model_dump() for g in body.goals]})
    row.version += 1
    audit(db, actor, "PERSONAL_ASSIGNMENT_UPDATED", user_id)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Concurrent account linking; reload") from exc
    return assignment_view(row)


@router.get("/access/personal/{user_id}")
def personal_assignment(
    user_id: UUID, actor: Actor = Depends(current_actor), db: Session = Depends(get_db)
):
    if not is_thana_admin(actor):
        raise HTTPException(403, "Main administrator required")
    if not db.get(AppUser, user_id):
        raise HTTPException(404, "Account not found")
    row = db.get(PersonalProfile, user_id)
    return assignment_view(row)


def assignment_view(row):
    # Management metadata only: main administrators do not automatically read private reports.
    return {
        "version": row.version if row else 0,
        "reviewer_id": str(row.reviewer_id) if row and row.reviewer_id else None,
        "member_id": str(row.member_id) if row and row.member_id else None,
        "goals": unpack(row.goals_encrypted).get("items", []) if row else [],
    }


@router.get("/self/reports/{report_id}/export/{extension}")
def export_own_report(
    report_id: UUID,
    extension: Literal["xlsx", "pdf"],
    actor: Actor = Depends(account_actor),
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response

    row = db.get(PersonalReport, report_id)
    if not row or row.user_id != actor.id:
        raise HTTPException(404, "Personal report not found")
    data = report_view(row, db.get(PersonalProfile, actor.id))
    if extension == "xlsx":
        from ..report_book import reporting_book_xlsx
        result = reporting_book_xlsx(data)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        from weasyprint import HTML

        from ..report_book import reporting_book_html
        profile = db.get(PersonalProfile, actor.id)
        name = unpack(profile.details_encrypted).get("full_name", "") if profile else ""
        html = reporting_book_html(data, name)
        result = HTML(string=html).write_pdf()
        media = "application/pdf"
    audit(db, actor, "SELF_REPORT_EXPORTED", row.id)
    db.commit()
    return Response(
        result,
        media_type=media,
        headers={
            "Content-Disposition": f'attachment; filename="my-report-{row.month}.{extension}"',
            "Cache-Control": "no-store",
        },
    )
