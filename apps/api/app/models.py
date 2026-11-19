import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


def uid():
    return uuid.uuid4()


def now():
    return datetime.now(timezone.utc)


class OrgNode(Base):
    __tablename__ = "org_nodes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uid)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("org_nodes.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(12), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (UniqueConstraint("parent_id", "code", name="uq_org_parent_code"),)


class AppUser(Base):
    __tablename__ = "app_users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uid)
    auth_sub: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


class RoleGrant(Base):
    __tablename__ = "role_grants"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("app_users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(24), nullable=False)
    scope_node_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("org_nodes.id"))
    __table_args__ = (UniqueConstraint("user_id", "role", "scope_node_id", name="uq_role_scope"),)


class Member(Base):
    __tablename__ = "members"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uid)
    member_number: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    father_name: Mapped[str | None] = mapped_column(String(200))
    phone_encrypted: Mapped[str | None] = mapped_column(Text)
    phone_digest: Mapped[str | None] = mapped_column(String(64), unique=True)
    address_encrypted: Mapped[str | None] = mapped_column(Text)
    occupation: Mapped[str | None] = mapped_column(String(160))
    position: Mapped[str | None] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    org_node_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("org_nodes.id"), nullable=False)
    joined_on: Mapped[date | None] = mapped_column(Date)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)
    __table_args__ = (Index("ix_members_scope_status_category", "org_node_id", "status", "category"),)


class ChangeRequest(Base):
    __tablename__ = "change_requests"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uid)
    member_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    proposed_value: Mapped[str] = mapped_column(String(128), nullable=False)
    original_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("app_users.id"), nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("app_users.id"))
    review_note: Mapped[str | None] = mapped_column(String(300))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MemberEvent(Base):
    __tablename__ = "member_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uid)
    member_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("members.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    before: Mapped[str | None] = mapped_column(String(128))
    after: Mapped[str | None] = mapped_column(String(128))
    actor_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("app_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    __table_args__ = (Index("ix_member_events_created", "created_at"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uid)
    actor_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("app_users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(72), nullable=False)
    target_id: Mapped[str] = mapped_column(String(40), nullable=False)
    detail: Mapped[str] = mapped_column(String(250), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)

class AccessRequest(Base):
    __tablename__ = "access_requests"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uid)
    auth_sub: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[str] = mapped_column(String(24), nullable=False)
    scope_node_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("org_nodes.id"))
    operation: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("app_users.id"), nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("app_users.id"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
