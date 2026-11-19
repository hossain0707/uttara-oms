import pytest
from pydantic import ValidationError
from app.schemas import MemberCreate, MemberRoutineUpdate, ChangePropose


def test_category_change_requires_supported_value():
    with pytest.raises(ValidationError):
        ChangePropose(kind="CATEGORY", proposed_value="")


def test_routine_patch_rejects_category_and_transfer():
    with pytest.raises(ValidationError):
        MemberRoutineUpdate(expected_version=1, category="RUKON")
    with pytest.raises(ValidationError):
        MemberRoutineUpdate(expected_version=1, org_node_id="fake")


def test_member_creation_requires_positive_consent_attestation():
    common = dict(member_number="T-001", full_name="Example", category="WORKER",
                  org_node_id="00000000-0000-0000-0000-000000000001",
                  consent_version="v1")
    with pytest.raises(ValidationError):
        MemberCreate(**common, consent_attested=False)
    assert MemberCreate(**common, consent_attested=True).consent_attested
