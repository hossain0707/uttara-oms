from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal


Category = Literal["RUKON", "WORKER", "ASSOCIATE", "SUPPORTER"]


class MemberCreate(BaseModel):
    member_number: str = Field(min_length=2, max_length=48)
    full_name: str = Field(min_length=2, max_length=200)
    father_name: str | None = Field(default=None, max_length=200)
    phone: str | None = None
    address: str | None = Field(default=None, max_length=1000)
    occupation: str | None = Field(default=None, max_length=160)
    position: str | None = Field(default=None, max_length=160)
    category: Category
    org_node_id: UUID
    joined_on: date | None = None
    consent_attested: Literal[True]
    consent_version: str = Field(min_length=1, max_length=32)


class MemberRoutineUpdate(BaseModel):
    expected_version: int = Field(ge=1)
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    father_name: str | None = Field(default=None, max_length=200)
    phone: str | None = None
    address: str | None = Field(default=None, max_length=1000)
    occupation: str | None = Field(default=None, max_length=160)
    position: str | None = Field(default=None, max_length=160)

    model_config = ConfigDict(extra="forbid")


class ChangePropose(BaseModel):
    kind: Literal["CATEGORY", "TRANSFER", "DEACTIVATE", "REACTIVATE"]
    proposed_value: str = Field(min_length=1, max_length=128)


class ChangeDecision(BaseModel):
    approve: bool
    note: str | None = Field(default=None, max_length=300)


class OrgCreate(BaseModel):
    parent_id: UUID | None = None
    kind: Literal["THANA", "WARD", "UNIT"]
    code: str = Field(min_length=1, max_length=40, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=160)


class OrgUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    active: bool | None = None
